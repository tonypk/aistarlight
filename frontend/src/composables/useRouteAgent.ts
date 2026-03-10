import { computed } from "vue";
import { useRoute } from "vue-router";

const ROUTE_AGENT_MAP: Record<string, string> = {
  "/reports": "filing",
  "/reconciliation": "recon",
  "/bank-reconciliation": "recon",
  "/classification": "classifier",
  "/journal-entries": "journal",
  "/general-ledger": "journal",
  "/accounts": "journal",
  "/statements": "filing",
  "/tax-bridge": "filing",
  "/calendar": "compliance",
  "/penalty-calculator": "compliance",
  "/form-router": "filing",
  "/chat": "general",
  "/withholding": "classifier",
  "/suppliers": "classifier",
  "/receipts": "classifier",
  "/upload": "general",
};

export function useRouteAgent() {
  const route = useRoute();

  const suggestedAgent = computed(() => {
    const path = route.path;
    for (const [routePrefix, agentId] of Object.entries(ROUTE_AGENT_MAP)) {
      if (path === routePrefix || path.startsWith(routePrefix + "/")) {
        return agentId;
      }
    }
    return "general";
  });

  const workflowType = computed(() => {
    const path = route.path;
    // Strip leading slash and take first segment
    const segment = path.split("/").filter(Boolean)[0];
    return segment || "";
  });

  return { suggestedAgent, workflowType };
}
