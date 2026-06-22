<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { api, apiBlob, canEdit, canManagePurpose, session } from '../api'

const stages = ['시료제작1', '시료제작2', '시료제작3', '촬영', '측정']
const purposes = ref([])
const error = ref('')
const newTitle = ref('')
const subProducts = ref([])
const selectedProduct = ref('')
const newSubProduct = ref('하위제품 1')
const adding = ref(false)
const uploading = ref('')
const fileInput = ref(null)
const selected = ref(null)
const preview = ref(null)
const previewImage = ref('')
const previewLoading = ref(false)
const previewError = ref('')
const openPurposeMenu = ref(null)
const editingPurpose = ref(null)
const editPurposeTitle = ref('')

const roleNotice = {
  viewer: '일반 유저는 S/U 완료된 표준을 열람할 수 있습니다.',
  engineer: '내부 관리자는 분석 목적과 PPTX 문서를 등록·삭제할 수 있습니다.',
  executive: '고위 관리자는 등록·삭제와 S/U 완료 처리를 할 수 있습니다.',
}

async function load() {
  if (!selectedProduct.value) return
  try { purposes.value = await api(`/purposes?sub_product=${encodeURIComponent(selectedProduct.value)}`) }
  catch { error.value = '로그인 후 분석 표준을 확인할 수 있습니다.' }
}

async function addPurpose() {
  if (!newTitle.value.trim()) return
  try {
    await api('/purposes', { method: 'POST', body: JSON.stringify({ title: newTitle.value, sub_product: newSubProduct.value }) })
    newTitle.value = ''; newSubProduct.value = selectedProduct.value; adding.value = false; load()
  } catch (e) { error.value = e.message }
}

function choose(purpose, stage) { selected.value = { purpose, stage }; fileInput.value.click() }

async function upload(e) {
  const file = e.target.files?.[0]
  if (!file) return
  const { purpose, stage } = selected.value
  uploading.value = `${purpose.id}-${stage}`
  const form = new FormData(); form.append('stage', stage); form.append('file', file)
  try { await api(`/purposes/${purpose.id}/documents`, { method: 'POST', body: form }); await load() }
  catch (err) { error.value = err.message }
  finally { uploading.value = ''; e.target.value = '' }
}

async function complete(purpose) {
  const nextStatus = purpose.status === 'complete' ? 'in_progress' : 'complete'
  try { await api(`/purposes/${purpose.id}`, { method: 'PATCH', body: JSON.stringify({ status: nextStatus }) }); load() }
  catch (e) { error.value = e.message }
}

async function removePurpose(purpose) {
  if (!window.confirm(`'${purpose.title}' 분석 목적과 연결된 모든 표준 파일을 삭제할까요?`)) return
  try { await api(`/purposes/${purpose.id}`, { method: 'DELETE' }); openPurposeMenu.value = null; await load() }
  catch (e) { error.value = e.message }
}

function openPurposeEdit(purpose) {
  openPurposeMenu.value = null
  editingPurpose.value = purpose
  editPurposeTitle.value = purpose.title
}

async function savePurposeTitle() {
  if (!editingPurpose.value || !editPurposeTitle.value.trim()) return
  try {
    await api(`/purposes/${editingPurpose.value.id}`, { method: 'PATCH', body: JSON.stringify({ title: editPurposeTitle.value }) })
    editingPurpose.value = null
    await load()
  } catch (e) { error.value = e.message }
}

function releasePreview() {
  if (previewImage.value) URL.revokeObjectURL(previewImage.value)
  previewImage.value = ''
}

async function openPreview(doc) {
  if (preview.value?.id === doc.id) return
  releasePreview()
  preview.value = doc; previewLoading.value = true; previewError.value = ''
  try {
    if (doc.thumbnail_url) previewImage.value = URL.createObjectURL(await apiBlob(doc.thumbnail_url))
    else previewError.value = '미리보기 이미지를 생성하지 못했습니다.'
  } catch (e) { previewError.value = e.message }
  finally { previewLoading.value = false }
}

function closePreview() { releasePreview(); preview.value = null; previewError.value = '' }

async function download(doc) {
  try {
    const url = URL.createObjectURL(await apiBlob(doc.file_url))
    const link = document.createElement('a'); link.href = url; link.download = doc.original_name
    document.body.appendChild(link); link.click(); link.remove(); URL.revokeObjectURL(url)
  } catch (e) { error.value = e.message }
}

async function removeDocument(purpose, stage) {
  if (!window.confirm(`'${stage}' 문서를 삭제할까요?`)) return
  try {
    await api(`/purposes/${purpose.id}/documents/${encodeURIComponent(stage)}`, { method: 'DELETE' })
    if (preview.value) closePreview()
    await load()
  } catch (e) { error.value = e.message }
}

function fill(doc) { return doc ? Math.max(0, 1 - doc.age_days / 10) : 0 }
function selectProduct(product) { selectedProduct.value = product; newSubProduct.value = product; closePreview(); load() }
async function loadProducts() {
  try {
    subProducts.value = await api('/sub-products')
    if (!selectedProduct.value && subProducts.value.length) {
      selectedProduct.value = subProducts.value[0].name
      newSubProduct.value = selectedProduct.value
    }
    await load()
  } catch (e) { error.value = e.message }
}
onMounted(loadProducts)
onBeforeUnmount(releasePreview)
</script>

<template>
  <section class="standards-wrap">
    <header class="page-intro">
      <div><p class="eyebrow">ANALYSIS LIBRARY</p><h1>분석 표준</h1><p>분석 목적별 표준 문서를 관리하고 각 단계의 최신 상태를 확인하세요.</p></div>
      <button v-if="canEdit()" class="primary add-btn" @click="adding = true">+ 분석 목적 등록</button>
    </header>
    <aside class="product-selector" aria-label="하위제품 선택">
      <p>하위제품 선택</p>
      <button v-for="product in subProducts" :key="product.id" :class="{ selected: selectedProduct === product.name }" @click="selectProduct(product.name)">
        <span class="product-dot"></span>{{ product.name }}
      </button>
    </aside>
    <div v-if="session.user" class="permission-note"><span>✦</span>{{ roleNotice[session.user.role] }}</div>
    <div v-if="error" class="error-banner">{{ error }}</div>

    <div v-if="purposes.length" class="standard-table">
      <div class="standard-head"><span>분석 목적</span><span v-for="stage in stages" :key="stage">{{ stage }}</span><span v-if="canManagePurpose()">상태</span></div>
      <div v-for="purpose in purposes" :key="purpose.id" class="standard-row">
        <div class="purpose-cell"><b>{{ purpose.title }}</b><small>{{ purpose.status === 'complete' ? 'S/U 완료' : 'S/U 진행 중' }}</small><template v-if="canManagePurpose()"><button class="purpose-more" title="분석 목적 메뉴" @click.stop="openPurposeMenu = openPurposeMenu === purpose.id ? null : purpose.id">···</button><div v-if="openPurposeMenu === purpose.id" class="purpose-menu"><button class="purpose-edit" @click="openPurposeEdit(purpose)">변경</button><button @click="removePurpose(purpose)">삭제</button></div></template></div>
        <div v-for="stage in stages" :key="stage" class="document-cell">
          <template v-if="purpose.documents[stage]">
            <button class="ppt-tile" :style="{ '--fill': fill(purpose.documents[stage]) }" @mouseenter="openPreview(purpose.documents[stage])" @click="openPreview(purpose.documents[stage])">
              <span class="ppt-icon">P</span><small>{{ purpose.documents[stage].age_days }}일 전</small>
            </button>
            <button class="document-more" title="문서 메뉴" @click="openPreview(purpose.documents[stage])">···</button>
          </template>
          <button v-else-if="canEdit()" class="empty-tile" @click="choose(purpose, stage)" :disabled="uploading === `${purpose.id}-${stage}`"><span>{{ uploading === `${purpose.id}-${stage}` ? '…' : '+' }}</span><small>업로드</small></button>
          <div v-else class="empty-readonly">—</div>
        </div>
        <div v-if="canManagePurpose()" class="status-cell"><button class="complete-btn" @click="complete(purpose)">{{ purpose.status === 'in_progress' ? 'S/U 완료' : 'S/U 진행' }}</button></div>
      </div>
    </div>
    <div v-else class="empty-state"><span>▤</span><h3>{{ session.user ? '표준이 아직 없습니다.' : '로그인이 필요합니다.' }}</h3><p>{{ session.user ? '새 분석 목적을 등록해 표준 관리를 시작하세요.' : error }}</p></div>

    <input ref="fileInput" class="file-input" type="file" accept=".pptx,application/vnd.openxmlformats-officedocument.presentationml.presentation" @change="upload" />
    <div v-if="adding" class="modal-backdrop" @click.self="adding = false"><form class="purpose-modal" @submit.prevent="addPurpose"><button type="button" class="close" @click="adding = false">×</button><p class="eyebrow">NEW ANALYSIS PURPOSE</p><h2>분석 목적 등록</h2><label>하위제품<select v-model="newSubProduct"><option v-for="product in subProducts" :key="product.id" :value="product.name">{{ product.name }}</option></select></label><label>분석 목적<input v-model="newTitle" maxlength="200" autofocus placeholder="예: 고온 보관 조건 신뢰성 분석" /></label><div class="form-actions"><button type="button" class="ghost" @click="adding = false">취소</button><button class="primary">등록하기</button></div></form></div>
    <div v-if="editingPurpose" class="modal-backdrop" @click.self="editingPurpose = null"><form class="purpose-modal" @submit.prevent="savePurposeTitle"><button type="button" class="close" @click="editingPurpose = null">×</button><p class="eyebrow">EDIT ANALYSIS PURPOSE</p><h2>분석 목적 변경</h2><label>분석 목적<input v-model="editPurposeTitle" maxlength="200" autofocus /></label><div class="form-actions"><button type="button" class="ghost" @click="editingPurpose = null">취소</button><button class="primary">변경 저장</button></div></form></div>

    <div v-if="preview" class="preview-popover" @click.self="closePreview">
      <button class="preview-close" @click="closePreview">×</button>
      <div v-if="previewLoading" class="preview-wait">미리보기를 불러오는 중입니다…</div>
      <img v-else-if="previewImage" :src="previewImage" alt="PPTX 첫 장 미리보기" />
      <div v-else class="preview-fallback">PPTX<br><small>{{ previewError || '미리보기 없음' }}</small></div>
      <div class="preview-info"><b>{{ preview.original_name }}</b><span>업로드 {{ preview.age_days }}일 경과</span></div>
      <div class="preview-actions"><button class="download-btn" @click="download(preview)">다운로드</button><button v-if="canEdit()" class="delete-btn" @click="removeDocument(purposes.find(p => p.documents[preview.stage]?.id === preview.id), preview.stage)">삭제</button></div>
    </div>
  </section>
</template>

<style scoped>
.document-cell { position: relative; }
.document-more { position: absolute; right: 5px; top: 4px; border: 0; background: transparent; color: #8290a8; font-size: 16px; line-height: 1; cursor: pointer; padding: 4px; }
.preview-popover { cursor: default; }
.preview-close { position: absolute; z-index: 1; right: 9px; top: 8px; width: 28px; height: 28px; border: 0; border-radius: 50%; background: #17253fb8; color: #fff; font-size: 21px; line-height: 24px; cursor: pointer; }
.preview-wait { width: 100%; aspect-ratio: 1.4; display: grid; place-items: center; background: #f5f7fc; color: #71809a; font-size: 13px; }
.preview-info { padding: 12px 15px; display: grid; gap: 3px; }
.preview-actions { display: flex; gap: 8px; padding: 0 15px 15px; }
.preview-actions button { flex: 1; border-radius: 8px; padding: 9px; border: 0; font: 600 12px 'Noto Sans KR'; cursor: pointer; }
.download-btn { background: #e9effd; color: #4564b4; }
.delete-btn { background: #fff0f1; color: #c84b5d; }
.purpose-cell { position: relative; }.purpose-more { position: absolute; top: 9px; right: 8px; border: 0; padding: 2px 5px; background: transparent; color: #9ca7b8; font-size: 17px; line-height: 1; cursor: pointer; }.purpose-menu { position: absolute; z-index: 4; top: 31px; right: 8px; min-width: 72px; padding: 4px; border: 1px solid #dfe5ee; border-radius: 7px; background: #fff; box-shadow: 0 8px 18px #1c2d4a1c; }.purpose-menu button { width: 100%; border: 0; border-radius: 5px; padding: 7px 8px; background: transparent; color: #c34e5c; text-align: left; font: 600 11px 'Noto Sans KR'; cursor: pointer; }.purpose-menu button:hover { background: #fff1f2; }.purpose-menu .purpose-edit { color: #526eb6; }.purpose-menu .purpose-edit:hover { background: #edf3ff; }
.product-selector { display: flex; align-items: center; justify-content: flex-end; gap: 8px; margin: -2px 0 20px; }.product-selector p { color: #78869c; font-size: 12px; font-weight: 600; margin: 0 4px 0 0; }.product-selector button { display: inline-flex; align-items: center; gap: 7px; border: 1px solid #dce3ee; border-radius: 9px; padding: 9px 12px; background: #fff; color: #69788e; font: 600 12px 'Noto Sans KR'; cursor: pointer; }.product-selector button.selected { border-color: #6d86cc; background: #eef3ff; color: #4864b1; }.product-dot { width: 7px; height: 7px; border-radius: 50%; background: #b7c4dc; }.selected .product-dot { background: #6380cc; }.purpose-modal select { border: 1px solid #dce3ee; border-radius: 8px; padding: 11px 12px; background: #fff; font: 14px 'Noto Sans KR'; outline-color: #6682ce; }
</style>
