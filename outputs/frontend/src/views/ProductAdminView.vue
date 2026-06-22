<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const products = ref([])
const name = ref('')
const error = ref('')
const saving = ref(false)

async function load() { try { products.value = await api('/admin/sub-products') } catch (e) { error.value = e.message } }
async function add() {
  if (!name.value.trim()) { error.value = '하위제품 이름을 입력해 주세요.'; return }
  saving.value = true
  try { await api('/admin/sub-products', { method: 'POST', body: JSON.stringify({ name: name.value, is_visible: true }) }); name.value = ''; error.value = ''; await load() }
  catch (e) { error.value = e.message }
  finally { saving.value = false }
}
async function toggle(product) { try { await api(`/admin/sub-products/${product.id}`, { method: 'PATCH', body: JSON.stringify({ is_visible: !product.is_visible }) }); await load() } catch (e) { error.value = e.message } }
async function remove(product) {
  if (!window.confirm(`'${product.name}'을 삭제할까요?\n등록된 분석 표준이 있으면 삭제할 수 없습니다.`)) return
  try { await api(`/admin/sub-products/${product.id}`, { method: 'DELETE' }); await load() } catch (e) { error.value = e.message }
}
onMounted(load)
</script>

<template>
  <section class="admin-wrap"><header class="page-intro"><div><p class="eyebrow">PRODUCT CATALOG</p><h1>제품 관리</h1><p>하위제품을 추가하고, viewer에게 표시할지와 삭제 가능 여부를 관리합니다.</p></div></header><div v-if="error" class="error-banner">{{ error }}</div>
    <div class="product-grid"><form class="product-form" @submit.prevent="add"><p class="form-title">하위제품 추가</p><label>하위제품 이름<input v-model="name" maxlength="100" placeholder="예: 하위제품 3" /></label><button class="primary" :disabled="saving">{{ saving ? '추가 중…' : '하위제품 추가' }}</button></form>
      <div class="product-list"><div class="list-header"><p class="form-title">등록된 하위제품</p><span>{{ products.length }}개</span></div><div v-if="products.length" class="items"><article v-for="product in products" :key="product.id" class="product-item"><div><span :class="product.is_visible ? 'published' : 'hidden'">{{ product.is_visible ? 'viewer 표시' : 'viewer 숨김' }}</span><h3>{{ product.name }}</h3></div><div class="product-actions"><button :class="product.is_visible ? 'unpublish' : 'publish'" @click="toggle(product)">{{ product.is_visible ? '숨기기' : '보이기' }}</button><button class="delete" @click="remove(product)">삭제</button></div></article></div><div v-else class="no-product">등록된 하위제품이 없습니다.</div></div>
    </div>
  </section>
</template>

<style scoped>
.admin-wrap{max-width:1260px;margin:0 auto;padding:48px 28px 72px}.product-grid{display:grid;grid-template-columns:minmax(280px,.8fr) minmax(380px,1.4fr);gap:22px;align-items:start}.product-form,.product-list{background:#fff;border:1px solid #e5eaf3;border-radius:14px;padding:23px}.form-title{margin:0;font-weight:700;font-size:16px;color:#2c3d5f}.product-form label{display:grid;gap:7px;margin-top:17px;color:#57667f;font-size:12px;font-weight:600}.product-form input{border:1px solid #dce3ee;border-radius:8px;padding:11px 12px;font:14px 'Noto Sans KR';outline-color:#6682ce}.product-form .primary{width:100%;margin-top:20px}.list-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}.list-header span{color:#8390a5;font-size:12px}.items{display:grid;gap:9px}.product-item{display:flex;justify-content:space-between;align-items:center;border:1px solid #e9edf4;border-radius:10px;padding:15px 16px}.product-item h3{margin:7px 0 0;font-size:14px}.product-item span{padding:3px 6px;border-radius:5px;font-size:10px;font-weight:600}.published{background:#e6f7ef;color:#319b71}.hidden{background:#f1f3f6;color:#7b8798}.product-actions{display:flex;gap:7px}.product-actions button{border:0;border-radius:7px;padding:7px 9px;font:600 11px 'Noto Sans KR';cursor:pointer}.unpublish{background:#fff0f1;color:#c74b5c}.publish{background:#e9effd;color:#4a66b4}.delete{background:#f0f2f6;color:#69778d}.no-product{border:1px dashed #d9e0ea;border-radius:9px;padding:45px;text-align:center;color:#8b97aa;font-size:13px}@media(max-width:760px){.admin-wrap{padding:28px 18px 50px}.product-grid{grid-template-columns:1fr}}
</style>
