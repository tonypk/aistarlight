/**
 * Receipt image compressor — light pre-upload compression.
 *
 * Two-phase strategy:
 *   Phase 1 (browser, this file): Light compression for upload bandwidth saving.
 *     - Resize to max 2048px (preserves OCR-critical detail)
 *     - Keep color (helps some OCR engines)
 *     - JPEG quality 80% (minimal artifact, good for OCR)
 *     - Canvas re-encoding strips EXIF metadata automatically
 *
 *   Phase 2 (Go server, after OCR): Aggressive compression for storage.
 *     - Resize to 1280px + grayscale + JPEG 55%
 *     - Only happens AFTER OCR has extracted all text
 *
 * Result: 10-15MB phone photo → ~500KB-1MB for upload (OCR-safe)
 *         → server compresses to ~100-300KB after OCR completes
 */

export interface CompressOptions {
  /** Maximum pixel dimension (width or height). Default: 2048 */
  maxDimension?: number;
  /** JPEG quality 0-1. Default: 0.80 */
  quality?: number;
  /** Convert to grayscale. Default: false (keep color for better OCR) */
  grayscale?: boolean;
  /** Target max file size in bytes. If exceeded, reduce quality further. Default: 2MB */
  maxFileSize?: number;
}

export interface CompressResult {
  blob: Blob;
  file: File;
  originalSize: number;
  compressedSize: number;
  ratio: number;
  width: number;
  height: number;
}

const DEFAULT_OPTIONS: Required<CompressOptions> = {
  maxDimension: 2048,
  quality: 0.8,
  grayscale: false,
  maxFileSize: 2 * 1024 * 1024, // 2MB — OCR-safe quality
};

/**
 * Load an image File into an HTMLImageElement.
 */
function loadImage(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(img.src);
      resolve(img);
    };
    img.onerror = () => {
      URL.revokeObjectURL(img.src);
      reject(new Error(`Failed to load image: ${file.name}`));
    };
    img.src = URL.createObjectURL(file);
  });
}

/**
 * Calculate scaled dimensions, preserving aspect ratio.
 */
function scaledSize(
  w: number,
  h: number,
  maxDim: number,
): { width: number; height: number } {
  if (w <= maxDim && h <= maxDim) return { width: w, height: h };
  const ratio = Math.min(maxDim / w, maxDim / h);
  return {
    width: Math.round(w * ratio),
    height: Math.round(h * ratio),
  };
}

/**
 * Draw image onto canvas with optional grayscale conversion.
 */
function drawToCanvas(
  img: HTMLImageElement,
  width: number,
  height: number,
  grayscale: boolean,
): HTMLCanvasElement {
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d")!;

  // Draw image
  ctx.drawImage(img, 0, 0, width, height);

  // Convert to grayscale via pixel manipulation
  if (grayscale) {
    const imageData = ctx.getImageData(0, 0, width, height);
    const data = imageData.data;
    for (let i = 0; i < data.length; i += 4) {
      // Luminosity formula: 0.299R + 0.587G + 0.114B
      const gray = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114;
      data[i] = gray;
      data[i + 1] = gray;
      data[i + 2] = gray;
      // alpha unchanged
    }
    ctx.putImageData(imageData, 0, 0);
  }

  return canvas;
}

/**
 * Convert canvas to JPEG blob at given quality.
 */
function canvasToBlob(
  canvas: HTMLCanvasElement,
  quality: number,
): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => {
        if (blob) resolve(blob);
        else reject(new Error("Canvas toBlob returned null"));
      },
      "image/jpeg",
      quality,
    );
  });
}

/**
 * Compress a single receipt image with extreme compression.
 *
 * If the image is already small enough (< 500KB), only light compression is applied.
 */
export async function compressReceiptImage(
  file: File,
  options?: CompressOptions,
): Promise<CompressResult> {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  const originalSize = file.size;

  // Skip tiny files (< 100KB) — already small enough
  if (originalSize < 100 * 1024) {
    return {
      blob: file,
      file,
      originalSize,
      compressedSize: originalSize,
      ratio: 1,
      width: 0,
      height: 0,
    };
  }

  const img = await loadImage(file);
  const { width, height } = scaledSize(
    img.naturalWidth,
    img.naturalHeight,
    opts.maxDimension,
  );

  const canvas = drawToCanvas(img, width, height, opts.grayscale);

  // First attempt at target quality
  let blob = await canvasToBlob(canvas, opts.quality);

  // If still too large, progressively reduce quality (min 0.30)
  let currentQuality = opts.quality;
  while (blob.size > opts.maxFileSize && currentQuality > 0.3) {
    currentQuality -= 0.05;
    blob = await canvasToBlob(canvas, currentQuality);
  }

  // If STILL too large, reduce dimensions further
  if (blob.size > opts.maxFileSize && opts.maxDimension > 800) {
    const smallerSize = scaledSize(img.naturalWidth, img.naturalHeight, 800);
    const smallerCanvas = drawToCanvas(
      img,
      smallerSize.width,
      smallerSize.height,
      opts.grayscale,
    );
    blob = await canvasToBlob(smallerCanvas, currentQuality);
  }

  // Build a new File with original name (extension changed to .jpg)
  const baseName = file.name.replace(/\.[^.]+$/, "");
  const compressedFile = new File([blob], `${baseName}.jpg`, {
    type: "image/jpeg",
  });

  return {
    blob,
    file: compressedFile,
    originalSize,
    compressedSize: blob.size,
    ratio: blob.size / originalSize,
    width,
    height,
  };
}

/**
 * Compress multiple receipt images in parallel (with concurrency limit).
 */
export async function compressBatch(
  files: File[],
  options?: CompressOptions,
  onProgress?: (done: number, total: number) => void,
): Promise<CompressResult[]> {
  const results: CompressResult[] = [];
  const CONCURRENCY = 3;
  let done = 0;

  // Process in batches of CONCURRENCY
  for (let i = 0; i < files.length; i += CONCURRENCY) {
    const batch = files.slice(i, i + CONCURRENCY);
    const batchResults = await Promise.all(
      batch.map((f) => compressReceiptImage(f, options)),
    );
    results.push(...batchResults);
    done += batch.length;
    onProgress?.(done, files.length);
  }

  return results;
}

/**
 * Format bytes to human-readable string.
 */
export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
