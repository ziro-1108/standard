<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const slots = [1, 2, 3]
const images = ref([])
const error = ref('')
const input = ref(null)
const selectedSlot = ref(null)
const uploading = ref(false)

async function load() { try { images.value = await api('/admin/home-images') } catch (e) { error.value = e.message } }
function imageFor(slot) { return images.value.find(image => image.slot === slot) }
function choose(slot) { selectedSlot.value = slot; input.value.click() }
async function upload(event) {
  const file = event.target.files?.[0]
  if (!file || !selectedSlot.value) return
  uploading.value = true
  const form = new FormData(); form.append('slot', String(selectedSlot.value)); form.append('file', file)
  try { await api('/admin/home-images', { method: 'POST', body: form }); await load() }
  catch (e) { error.value = e.message }
  finally { uploading.value = false; event.target.value = ''; selectedSlot.value = null }
}
async function toggle(image) { try { await api(`/admin/home-images/${image.id}`, { method: 'PATCH', body: JSON.stringify({ is_visible: !image.is_visible }) }); await load() } catch (e) { error.value = e.message } }
async function remove(image) { if (!window.confirm(`'${image.original_name}' 이미지를 삭제할까요?`)) return; try { await api(`/admin/home-images/${image.id}`, { method: 'DELETE' }); await load() } catch (e) { error.value = e.message } }
onMounted(load)
</script>

<template>
  <section class="server-wrap"><header class="page-intro"><div><p class="eyebrow">HOME VISUAL CONSOLE</p><h1>서버 관리</h1><p>홈페이지 슬라이더 1~3번 이미지를 업로드하고 공개 상태를 관리합니다.</p></div></header><div v-if="error" class="error-banner">{{ error }}</div>
    <div class="image-grid"><article v-for="slot in slots" :key="slot" class="image-card"><div class="slot-label">HOME IMAGE {{ slot }}</div><img v-if="imageFor(slot)" :src="imageFor(slot).image_url" :alt="`홈 이미지 ${slot}`" /><div v-else class="image-empty"><span>▧</span><p>이미지가 없습니다</p></div><div class="image-info"><b>{{ imageFor(slot)?.original_name || `슬라이더 ${slot}번` }}</b><small v-if="imageFor(slot)" :class="imageFor(slot).is_visible ? 'visible' : 'hidden'">{{ imageFor(slot).is_visible ? '홈에 표시 중' : '홈에서 숨김' }}</small><small v-else>JPG · PNG · WebP</small></div><div class="image-actions"><button class="upload" :disabled="uploading" @click="choose(slot)">{{ imageFor(slot) ? '교체 업로드' : '이미지 업로드' }}</button><template v-if="imageFor(slot)"><button :class="imageFor(slot).is_visible ? 'hide' : 'show'" @click="toggle(imageFor(slot))">{{ imageFor(slot).is_visible ? '숨기기' : '보이기' }}</button><button class="delete" @click="remove(imageFor(slot))">삭제</button></template></div></article></div>
    <input ref="input" class="file-input" type="file" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" @change="upload" />
    <aside class="design-guide"><p class="eyebrow">IMAGE STYLE GUIDE</p><h2>기존 홈 이미지와 어울리게 만들려면</h2><div class="guide-grid"><div><b>권장 비율</b><span>1600 × 700px, 가로형 16:7</span></div><div><b>안전 영역</b><span>좌측 45%는 제목이 놓일 여백으로 비워두세요.</span></div><div><b>색감</b><span>블루·라벤더·코랄 계열의 밝고 차분한 톤을 추천합니다.</span></div><div><b>파일 형식</b><span>WebP 또는 PNG, 10MB 이하로 저장하세요.</span></div></div></aside>
  </section>
</template>

<style scoped>
.server-wrap{max-width:1260px;margin:0 auto;padding:48px 28px 72px}.image-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.image-card{overflow:hidden;background:#fff;border:1px solid #e5eaf3;border-radius:14px}.slot-label{padding:10px 14px;background:#f6f8fc;color:#73819a;font:500 10px 'DM Mono';letter-spacing:1px}.image-card img,.image-empty{display:block;width:100%;aspect-ratio:16/7;object-fit:cover}.image-empty{display:grid;place-items:center;background:#f7f9fc;color:#9aa7b9;text-align:center}.image-empty span{font-size:28px}.image-empty p{margin:2px 0 0;font-size:12px}.image-info{display:grid;gap:5px;padding:13px 14px}.image-info b{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px}.image-info small{font-size:11px;color:#8490a4}.visible{color:#35a278!important}.hidden{color:#8793a5}.image-actions{display:flex;gap:6px;padding:0 14px 14px}.image-actions button{border:0;border-radius:7px;padding:8px 8px;font:600 11px 'Noto Sans KR';cursor:pointer}.upload{background:#e9effd;color:#4564b4}.hide{background:#fff0f1;color:#c74b5c}.show{background:#e6f7ef;color:#319b71}.delete{background:#f0f2f6;color:#69778d}.design-guide{margin-top:28px;padding:25px;border:1px solid #e1e8f5;border-radius:14px;background:#f8faff}.design-guide h2{margin:0 0 18px;font-size:19px;letter-spacing:-.8px}.guide-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.guide-grid div{display:grid;gap:5px}.guide-grid b{font-size:12px;color:#465f9e}.guide-grid span{font-size:12px;color:#718097;line-height:1.6}@media(max-width:800px){.server-wrap{padding:28px 18px 50px}.image-grid,.guide-grid{grid-template-columns:1fr}.image-card img,.image-empty{aspect-ratio:16/7}}
</style>
