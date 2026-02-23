<script setup lang="ts">
import { ref } from 'vue'

const activeSection = ref('overview')

const sections = [
  { id: 'overview', title: '系统概览' },
  { id: 'quickstart', title: '快速入门' },
  { id: 'upload', title: '上传数据' },
  { id: 'mapping', title: '列映射' },
  { id: 'classification', title: '交易分类' },
  { id: 'reconciliation', title: 'VAT 对账' },
  { id: 'reports', title: '报表生成' },
  { id: 'edit-report', title: '编辑报表' },
  { id: 'suppliers', title: '供应商管理' },
  { id: 'withholding', title: '扣缴税（EWT）' },
  { id: 'chat', title: 'AI 税务助手' },
  { id: 'knowledge', title: '知识库' },
  { id: 'faq', title: '常见问题' },
]

function scrollTo(id: string) {
  activeSection.value = id
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>

<template>
  <div class="guide-view">
    <div class="guide-header">
      <h2>操作指南</h2>
      <p class="subtitle">AIStarlight 菲律宾税务助手 — 完整使用教程</p>
    </div>

    <div class="guide-layout">
      <!-- Table of Contents -->
      <nav class="toc">
        <h4>目录</h4>
        <a
          v-for="s in sections"
          :key="s.id"
          :class="{ active: activeSection === s.id }"
          @click.prevent="scrollTo(s.id)"
          href="#"
        >{{ s.title }}</a>
      </nav>

      <!-- Content -->
      <div class="content">

        <!-- 1. Overview -->
        <section id="overview">
          <h3>1. 系统概览</h3>
          <p>AIStarlight 是一款 AI 驱动的菲律宾税务申报助手，帮助您完成以下工作：</p>
          <div class="feature-grid">
            <div class="feature-item">
              <span class="fi">📤</span>
              <div>
                <strong>数据上传</strong>
                <p>支持 Excel、CSV 格式的销售和采购数据</p>
              </div>
            </div>
            <div class="feature-item">
              <span class="fi">🤖</span>
              <div>
                <strong>AI 智能映射</strong>
                <p>自动识别列名，将数据映射到 BIR 表单字段</p>
              </div>
            </div>
            <div class="feature-item">
              <span class="fi">🏷️</span>
              <div>
                <strong>交易分类</strong>
                <p>AI 自动分类 VAT 类型（Vatable / Exempt / Zero-rated）</p>
              </div>
            </div>
            <div class="feature-item">
              <span class="fi">🔍</span>
              <div>
                <strong>VAT 对账</strong>
                <p>销售与采购交叉核对，发现异常</p>
              </div>
            </div>
            <div class="feature-item">
              <span class="fi">📋</span>
              <div>
                <strong>BIR 报表</strong>
                <p>自动计算并生成 BIR 2550M / 2550Q / 1601C / 0619E PDF</p>
              </div>
            </div>
            <div class="feature-item">
              <span class="fi">📑</span>
              <div>
                <strong>扣缴税管理</strong>
                <p>EWT 分类、BIR 2307 证书生成、SAWT 汇总</p>
              </div>
            </div>
          </div>

          <div class="info-box">
            <strong>支持的 BIR 表单：</strong>
            <ul>
              <li><strong>BIR 2550M</strong> — 月度增值税申报</li>
              <li><strong>BIR 2550Q</strong> — 季度增值税申报</li>
              <li><strong>BIR 1601-C</strong> — 月度薪资扣缴税汇缴</li>
              <li><strong>BIR 0619-E</strong> — 月度扩展扣缴税汇缴</li>
              <li><strong>BIR 2307</strong> — 扣缴税证书</li>
              <li><strong>SAWT</strong> — 扣缴税汇总附表</li>
            </ul>
          </div>
        </section>

        <!-- 2. Quick Start -->
        <section id="quickstart">
          <h3>2. 快速入门</h3>
          <p>第一次使用？按以下步骤操作：</p>
          <div class="steps">
            <div class="step">
              <span class="step-num">1</span>
              <div>
                <strong>设置公司信息</strong>
                <p>进入 <router-link to="/settings">Settings</router-link>，填写公司名称、TIN 号码和 RDO 代码。这些信息会打印在 PDF 报表上。</p>
              </div>
            </div>
            <div class="step">
              <span class="step-num">2</span>
              <div>
                <strong>上传数据文件</strong>
                <p>进入 <router-link to="/upload">Upload Data</router-link>，上传包含销售和采购记录的 Excel 或 CSV 文件。</p>
              </div>
            </div>
            <div class="step">
              <span class="step-num">3</span>
              <div>
                <strong>确认列映射</strong>
                <p>系统 AI 会自动识别您的列名。审查并确认映射结果。</p>
              </div>
            </div>
            <div class="step">
              <span class="step-num">4</span>
              <div>
                <strong>生成报表</strong>
                <p>进入 <router-link to="/reports">Reports</router-link>，选择表单类型和期间，点击 "Generate Report"。</p>
              </div>
            </div>
            <div class="step">
              <span class="step-num">5</span>
              <div>
                <strong>审查并下载 PDF</strong>
                <p>检查计算结果，如需修改可编辑字段。确认无误后下载 PDF 用于申报。</p>
              </div>
            </div>
          </div>
        </section>

        <!-- 3. Upload -->
        <section id="upload">
          <h3>3. 上传数据</h3>
          <p>路径：侧边栏 → <strong>Upload Data</strong></p>

          <h4>支持的文件格式</h4>
          <ul>
            <li>Excel 文件（.xlsx, .xls）</li>
            <li>CSV 文件（.csv）</li>
            <li>PDF 文件（.pdf）— 系统会尝试提取表格数据</li>
          </ul>

          <h4>数据要求</h4>
          <ul>
            <li>文件需包含 <strong>金额</strong>（Amount）列</li>
            <li>建议包含：日期、描述/备注、增值税金额、增值税类型</li>
            <li>销售数据和采购数据可以在同一文件的不同 Sheet 中</li>
          </ul>

          <div class="tip-box">
            <strong>提示：</strong>上传后可选择 Sheet 名称（多 Sheet 文件），系统会预览前几行数据供确认。
          </div>
        </section>

        <!-- 4. Mapping -->
        <section id="mapping">
          <h3>4. 列映射</h3>
          <p>路径：上传文件后自动跳转，或侧边栏 → <strong>Upload Data</strong> → 选择文件</p>

          <h4>工作原理</h4>
          <ol>
            <li>上传文件后，AI 会分析您的列名（如 "Sales Amount"、"VAT"、"Date" 等）</li>
            <li>AI 自动推荐映射方案，将您的列名对应到系统字段</li>
            <li>您可以手动调整映射结果</li>
            <li>确认映射后，数据将被解析并用于后续计算</li>
          </ol>

          <h4>系统字段说明</h4>
          <table class="ref-table">
            <thead>
              <tr><th>字段</th><th>说明</th><th>必填</th></tr>
            </thead>
            <tbody>
              <tr><td>amount</td><td>交易金额</td><td>是</td></tr>
              <tr><td>vat_amount</td><td>增值税金额</td><td>否（系统可按 12% 计算）</td></tr>
              <tr><td>vat_type</td><td>VAT 类型：vatable / exempt / zero_rated / government</td><td>否（AI 可自动分类）</td></tr>
              <tr><td>date</td><td>交易日期</td><td>否</td></tr>
              <tr><td>description</td><td>交易描述</td><td>否（用于 AI 分类）</td></tr>
              <tr><td>category</td><td>采购类别：goods / services / capital / imports</td><td>否</td></tr>
            </tbody>
          </table>
        </section>

        <!-- 5. Classification -->
        <section id="classification">
          <h3>5. 交易分类</h3>
          <p>路径：侧边栏 → <strong>Classification</strong></p>

          <h4>创建对账会话</h4>
          <ol>
            <li>点击 "New Session"，输入会话名称和期间</li>
            <li>上传销售数据文件和采购数据文件</li>
            <li>系统解析文件后生成交易列表</li>
          </ol>

          <h4>AI 自动分类</h4>
          <p>点击 "Classify" 按钮，AI 会自动：</p>
          <ul>
            <li>识别每笔交易的 VAT 类型（Vatable / Exempt / Zero-rated / Government）</li>
            <li>分类采购类别（Goods / Services / Capital / Imports）</li>
            <li>标记低置信度的分类供人工审查</li>
          </ul>

          <div class="tip-box">
            <strong>提示：</strong>您可以手动修改任何一笔交易的分类结果。系统会学习您的修改模式。
          </div>
        </section>

        <!-- 6. Reconciliation -->
        <section id="reconciliation">
          <h3>6. VAT 对账</h3>
          <p>路径：侧边栏 → <strong>Reconciliation</strong></p>

          <h4>对账流程</h4>
          <ol>
            <li>交易分类完成后，点击 "Reconcile" 开始对账</li>
            <li>系统会交叉核对销售和采购记录</li>
            <li>生成 VAT 汇总：Output VAT、Input VAT、Net VAT Payable</li>
            <li>检测异常：金额不匹配、缺失交易、重复记录</li>
          </ol>

          <h4>对账完成后可以：</h4>
          <ul>
            <li><strong>Generate BIR Report</strong> — 直接从对账数据生成 BIR 2550M/2550Q 报表</li>
            <li><strong>Export PDF</strong> — 导出完整对账报告 PDF（包含 VAT 汇总、匹配统计、异常清单）</li>
            <li><strong>Export CSV</strong> — 导出交易数据 CSV</li>
          </ul>
        </section>

        <!-- 7. Reports -->
        <section id="reports">
          <h3>7. 报表生成</h3>
          <p>路径：侧边栏 → <strong>Reports</strong></p>

          <h4>生成报表</h4>
          <ol>
            <li>选择 <strong>表单类型</strong>（BIR 2550M / 2550Q / 1601C / 0619E）</li>
            <li>选择 <strong>申报期间</strong>（月份或季度）</li>
            <li>数据来源：
              <ul>
                <li>从已上传的文件（自动使用列映射结果）</li>
                <li>从对账会话（Reconciliation → Generate Report）</li>
                <li>手动输入数据</li>
              </ul>
            </li>
            <li>点击 "Generate Report" — 系统自动计算所有字段并生成 PDF</li>
          </ol>

          <h4>报表工作流</h4>
          <div class="workflow">
            <span class="wf-step">Draft</span>
            <span class="wf-arrow">&rarr;</span>
            <span class="wf-step">Review</span>
            <span class="wf-arrow">&rarr;</span>
            <span class="wf-step">Approved</span>
            <span class="wf-arrow">&rarr;</span>
            <span class="wf-step">Filed</span>
            <span class="wf-arrow">&rarr;</span>
            <span class="wf-step">Archived</span>
          </div>
          <ul>
            <li><strong>Draft</strong> — 可编辑，可修改字段值</li>
            <li><strong>Review</strong> — 提交审核，仍可编辑</li>
            <li><strong>Approved</strong> — 审核通过，准备申报</li>
            <li><strong>Filed</strong> — 已向 BIR 提交</li>
            <li><strong>Archived</strong> — 归档保存</li>
          </ul>
        </section>

        <!-- 8. Edit Report -->
        <section id="edit-report">
          <h3>8. 编辑报表</h3>
          <p>在报表列表中点击 "Edit" 按钮进入编辑页面。</p>

          <h4>编辑功能</h4>
          <ul>
            <li>可修改任何可编辑字段（如销售额、输入税等）</li>
            <li>系统自动重算所有关联字段（如修改 Vatable Sales 会自动更新 Output VAT、Total Sales、VAT Payable 等）</li>
            <li>每次编辑自动记录审计日志</li>
            <li>使用乐观锁（版本号）防止并发冲突</li>
            <li>首次编辑时自动保存原始计算数据，方便对比</li>
          </ul>

          <div class="warning-box">
            <strong>注意：</strong>编辑后 PDF 会自动重新生成。已经进入 "Filed" 或 "Archived" 状态的报表不可编辑。
          </div>
        </section>

        <!-- 9. Suppliers -->
        <section id="suppliers">
          <h3>9. 供应商管理</h3>
          <p>路径：侧边栏 → <strong>Suppliers</strong></p>

          <h4>管理供应商</h4>
          <ul>
            <li><strong>添加供应商</strong> — 填写 TIN、名称、地址、类型（个人/公司）</li>
            <li><strong>设置默认 EWT</strong> — 为供应商设置默认扣缴税率和 ATC 代码</li>
            <li><strong>批量匹配</strong> — 在 EWT 分类时，系统会自动匹配已有供应商</li>
          </ul>

          <h4>供应商字段说明</h4>
          <table class="ref-table">
            <thead>
              <tr><th>字段</th><th>说明</th></tr>
            </thead>
            <tbody>
              <tr><td>TIN</td><td>供应商税号（Tax Identification Number）</td></tr>
              <tr><td>Name</td><td>供应商全名</td></tr>
              <tr><td>Type</td><td>Individual（个人）或 Corporation（公司）</td></tr>
              <tr><td>Default EWT Rate</td><td>默认扣缴税率（如 0.02 = 2%）</td></tr>
              <tr><td>Default ATC Code</td><td>默认 ATC 代码（如 WC050）</td></tr>
              <tr><td>VAT Registered</td><td>是否注册增值税</td></tr>
            </tbody>
          </table>
        </section>

        <!-- 10. Withholding Tax -->
        <section id="withholding">
          <h3>10. 扣缴税（EWT）管理</h3>
          <p>路径：侧边栏 → <strong>Withholding Tax</strong></p>

          <h4>EWT 工作流程</h4>
          <div class="steps">
            <div class="step">
              <span class="step-num">1</span>
              <div>
                <strong>分类 EWT</strong>
                <p>在对账会话中，点击 "Classify EWT" 对采购交易自动识别 ATC 代码和扣缴税率</p>
              </div>
            </div>
            <div class="step">
              <span class="step-num">2</span>
              <div>
                <strong>生成 BIR 2307</strong>
                <p>点击 "Generate Certificates"，系统自动按供应商和期间汇总，生成 BIR 2307 扣缴税证书 PDF</p>
              </div>
            </div>
            <div class="step">
              <span class="step-num">3</span>
              <div>
                <strong>下载 SAWT</strong>
                <p>在 Withholding Tax 页面选择期间，下载 SAWT 汇总附表（CSV 或 PDF 格式）</p>
              </div>
            </div>
            <div class="step">
              <span class="step-num">4</span>
              <div>
                <strong>生成 0619-E</strong>
                <p>在 Reports 页面选择 BIR 0619-E，系统自动汇总月度 EWT 金额</p>
              </div>
            </div>
          </div>

          <h4>常用 ATC 代码参考</h4>
          <table class="ref-table">
            <thead>
              <tr><th>ATC 代码</th><th>说明</th><th>税率</th></tr>
            </thead>
            <tbody>
              <tr><td>WC010</td><td>专业费用 — 公司</td><td>10%</td></tr>
              <tr><td>WI010</td><td>专业费用 — 个人 (&lt;3M)</td><td>5%</td></tr>
              <tr><td>WI050 / WC050</td><td>承包商 / 分包商</td><td>2%</td></tr>
              <tr><td>WI030</td><td>租金 — 不动产</td><td>5%</td></tr>
              <tr><td>WC060</td><td>广告 / 推广</td><td>2%</td></tr>
              <tr><td>WI100 / WC100</td><td>采购商品 (&gt;3M/年)</td><td>1%</td></tr>
              <tr><td>WI120 / WC120</td><td>服务费</td><td>2%</td></tr>
            </tbody>
          </table>
        </section>

        <!-- 11. AI Chat -->
        <section id="chat">
          <h3>11. AI 税务助手</h3>
          <p>路径：侧边栏 → <strong>AI Chat</strong></p>

          <p>您可以用中文或英文向 AI 助手提问任何菲律宾税务相关问题，例如：</p>
          <ul>
            <li>"BIR 2550M 的申报截止日期是什么时候？"</li>
            <li>"什么情况下可以申请 VAT 退税？"</li>
            <li>"专业服务费的扣缴税率是多少？"</li>
            <li>"TRAIN Law 对个人所得税有什么影响？"</li>
            <li>"BIR 2307 和 SAWT 的区别是什么？"</li>
          </ul>

          <div class="tip-box">
            <strong>提示：</strong>AI 助手的回答基于菲律宾 NIRC、TRAIN Law、CREATE Act 和 BIR 官方法规。系统支持长期记忆——您可以在 Memory 页面管理 AI 的记忆。
          </div>
        </section>

        <!-- 12. Knowledge -->
        <section id="knowledge">
          <h3>12. 知识库</h3>
          <p>路径：侧边栏 → <strong>Knowledge</strong></p>

          <p>知识库包含菲律宾税务法律法规的结构化数据，用于增强 AI 助手的回答准确性。</p>

          <h4>内置知识</h4>
          <ul>
            <li>NIRC（菲律宾国内税收法典）— VAT 相关章节</li>
            <li>TRAIN Law (RA 10963) — 税制改革要点</li>
            <li>CREATE Act (RA 11534) — 企业所得税优惠</li>
            <li>BIR Revenue Regulations — EWT、申报规则等</li>
            <li>BIR 各类表单填写指南</li>
            <li>罚款与补救措施</li>
          </ul>

          <p>您可以在知识库页面搜索相关内容，查看具体条文和规定。</p>
        </section>

        <!-- 13. FAQ -->
        <section id="faq">
          <h3>13. 常见问题</h3>

          <div class="faq-item">
            <h4>Q: 报表数据计算错误怎么办？</h4>
            <p>A: 在报表列表中点击 "Edit" 进入编辑页面，修改相应字段。系统会自动重算所有关联字段并重新生成 PDF。</p>
          </div>

          <div class="faq-item">
            <h4>Q: 可以修改已提交的报表吗？</h4>
            <p>A: Draft 和 Review 状态的报表可以编辑。Approved 及之后状态的报表不可修改。如需修改，请先将状态退回到 Draft。</p>
          </div>

          <div class="faq-item">
            <h4>Q: 文件上传失败怎么办？</h4>
            <p>A: 请确认文件格式为 .xlsx、.xls、.csv 或 .pdf，文件大小不超过 10MB。如果是 Excel 文件，确保数据在第一个 Sheet 或指定的 Sheet 名称中。</p>
          </div>

          <div class="faq-item">
            <h4>Q: AI 分类结果不准确怎么办？</h4>
            <p>A: 手动修改分类结果。系统会学习您的修改模式，后续分类会更准确。您也可以为供应商设置默认的 EWT 税率和 ATC 代码。</p>
          </div>

          <div class="faq-item">
            <h4>Q: 如何更改公司信息（TIN、RDO）？</h4>
            <p>A: 进入 Settings 页面修改。更改后生成的新报表会使用新的公司信息，已生成的报表不受影响。</p>
          </div>

          <div class="faq-item">
            <h4>Q: BIR 2550M 和 2550Q 有什么区别？</h4>
            <p>A: 2550M 是月度 VAT 申报，2550Q 是季度 VAT 申报。计算逻辑相同，区别在于申报期间和数据范围。</p>
          </div>
        </section>

      </div>
    </div>
  </div>
</template>

<style scoped>
.guide-view {
  max-width: 1200px;
}

.guide-header {
  margin-bottom: 24px;
}
.guide-header h2 {
  margin-bottom: 4px;
}
.subtitle {
  color: #888;
  font-size: 14px;
}

.guide-layout {
  display: flex;
  gap: 24px;
}

/* Table of Contents */
.toc {
  width: 180px;
  flex-shrink: 0;
  position: sticky;
  top: 24px;
  align-self: flex-start;
  background: #fff;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}
.toc h4 {
  margin-bottom: 12px;
  color: #374151;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.toc a {
  display: block;
  padding: 6px 10px;
  color: #6b7280;
  text-decoration: none;
  font-size: 13px;
  border-radius: 4px;
  transition: all 0.15s;
}
.toc a:hover {
  color: #4f46e5;
  background: #f5f3ff;
}
.toc a.active {
  color: #4f46e5;
  background: #eef2ff;
  font-weight: 500;
}

/* Content */
.content {
  flex: 1;
  min-width: 0;
}

section {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  margin-bottom: 16px;
}

section h3 {
  font-size: 18px;
  margin-bottom: 12px;
  color: #111827;
  padding-bottom: 8px;
  border-bottom: 1px solid #f3f4f6;
}

section h4 {
  font-size: 15px;
  margin: 16px 0 8px;
  color: #374151;
}

section p {
  color: #4b5563;
  line-height: 1.6;
  margin-bottom: 8px;
}

section ul, section ol {
  padding-left: 20px;
  color: #4b5563;
  line-height: 1.8;
}

section li {
  margin-bottom: 4px;
}

/* Feature Grid */
.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
  margin: 16px 0;
}
.feature-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #f3f4f6;
}
.feature-item .fi {
  font-size: 24px;
  flex-shrink: 0;
}
.feature-item strong {
  display: block;
  font-size: 14px;
  margin-bottom: 2px;
}
.feature-item p {
  font-size: 13px;
  color: #6b7280;
  margin: 0;
}

/* Steps */
.steps {
  margin: 16px 0;
}
.step {
  display: flex;
  gap: 16px;
  padding: 14px 0;
  border-bottom: 1px solid #f3f4f6;
}
.step:last-child {
  border-bottom: none;
}
.step-num {
  width: 32px;
  height: 32px;
  background: #4f46e5;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}
.step strong {
  display: block;
  margin-bottom: 4px;
}
.step p {
  font-size: 14px;
  margin: 0;
}

/* Info, Tip, Warning boxes */
.info-box, .tip-box, .warning-box {
  padding: 14px 16px;
  border-radius: 8px;
  margin: 16px 0;
  font-size: 14px;
  line-height: 1.6;
}
.info-box {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #1e40af;
}
.info-box ul {
  margin-top: 8px;
  color: #1e40af;
}
.tip-box {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
}
.warning-box {
  background: #fffbeb;
  border: 1px solid #fde68a;
  color: #92400e;
}

/* Reference tables */
.ref-table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 14px;
}
.ref-table th {
  text-align: left;
  padding: 8px 12px;
  background: #f9fafb;
  color: #374151;
  font-weight: 600;
  border-bottom: 2px solid #e5e7eb;
}
.ref-table td {
  padding: 8px 12px;
  border-bottom: 1px solid #f3f4f6;
  color: #4b5563;
}

/* Workflow */
.workflow {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 16px 0;
  flex-wrap: wrap;
}
.wf-step {
  padding: 6px 14px;
  background: #eef2ff;
  color: #4f46e5;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}
.wf-arrow {
  color: #9ca3af;
  font-size: 18px;
}

/* FAQ */
.faq-item {
  padding: 12px 0;
  border-bottom: 1px solid #f3f4f6;
}
.faq-item:last-child {
  border-bottom: none;
}
.faq-item h4 {
  color: #111827;
  margin: 0 0 6px;
}
.faq-item p {
  margin: 0;
  font-size: 14px;
}

/* Responsive */
@media (max-width: 768px) {
  .guide-layout {
    flex-direction: column;
  }
  .toc {
    width: 100%;
    position: static;
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }
  .toc h4 {
    width: 100%;
  }
}
</style>
