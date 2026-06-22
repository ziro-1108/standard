<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

const roles = [
  { key: 'engineer', label: '내부 엔지니어' }, { key: 'executive', label: '고위 관리자' }, { key: 'server_admin', label: '서버 관리자' },
]
const accounts = ref([])
const selectedRole = ref('engineer')
const selectedIds = ref([])
const error = ref('')
const addOpen = ref(false)
const changeOpen = ref(false)
const addAccount = ref('')
const addRole = ref('engineer')
const changing = ref(null)
const changeRole = ref('viewer')
const filtered = computed(() => accounts.value.filter(account => account.role === selectedRole.value))

async function load() { try { accounts.value = await api('/admin/managed-accounts'); selectedIds.value = [] } catch (e) { error.value = e.message } }
function selectRole(role) { selectedRole.value = role; selectedIds.value = [] }
async function createAccount() {
  try { await api('/admin/managed-accounts', { method: 'POST', body: JSON.stringify({ ad_account: addAccount.value, role: addRole.value }) }); addOpen.value = false; addAccount.value = ''; await load() } catch (e) { error.value = e.message }
}
function openChange(account) { changing.value = account; changeRole.value = account.role; changeOpen.value = true }
async function updateRole() { try { await api(`/admin/managed-accounts/${changing.value.id}`, { method: 'PATCH', body: JSON.stringify({ role: changeRole.value }) }); changeOpen.value = false; await load() } catch (e) { error.value = e.message } }
async function removeSelected() {
  if (!selectedIds.value.length) return
  if (!window.confirm(`선택한 ${selectedIds.value.length}개 AD 계정을 관리 목록에서 제거할까요?\n제거된 계정은 Viewer로 처리됩니다.`)) return
  try { await api('/admin/managed-accounts', { method: 'DELETE', body: JSON.stringify({ ids: selectedIds.value }) }); await load() } catch (e) { error.value = e.message }
}
onMounted(load)
</script>

<template>
  <section class="permission-wrap"><header class="page-intro"><div><p class="eyebrow">AD ACCESS CONTROL</p><h1>권한 관리</h1><p>AD 계정명 기준으로 시스템 권한을 관리합니다. 목록에 없는 계정은 Viewer로 처리됩니다.</p></div><button class="primary" @click="addOpen = true">+ AD 계정 추가</button></header><div v-if="error" class="error-banner">{{ error }}</div>
    <div class="permission-guide"><b>토큰 연동 방식</b><span>인증 토큰의 <code>ad_account</code> 값을 관리 목록과 비교해 권한을 결정합니다.</span></div>
    <div class="role-tabs"><button v-for="role in roles" :key="role.key" :class="{ active: selectedRole === role.key }" @click="selectRole(role.key)">{{ role.label }} <small>{{ accounts.filter(a => a.role === role.key).length }}</small></button></div>
    <div class="account-panel"><div class="panel-head"><div><b>{{ roles.find(r => r.key === selectedRole)?.label }} 관리 목록</b><span>{{ filtered.length }}개 AD 계정</span></div><button class="bulk-delete" :disabled="!selectedIds.length" @click="removeSelected">선택 제거 ({{ selectedIds.length }})</button></div><div v-if="filtered.length" class="account-table"><div class="account-head"><span></span><span>AD 계정명</span><span>등록일</span><span>관리</span></div><div v-for="account in filtered" :key="account.id" class="account-row"><span><input v-model="selectedIds" type="checkbox" :value="account.id" /></span><b>{{ account.ad_account }}</b><time>{{ new Date(account.created_at).toLocaleDateString('ko-KR') }}</time><button class="change-btn" @click="openChange(account)">권한 변경</button></div></div><div v-else class="empty-list">이 직급에 관리 중인 AD 계정이 없습니다.</div></div>
  </section>
  <div v-if="addOpen" class="modal-backdrop" @click.self="addOpen = false"><form class="access-modal" @submit.prevent="createAccount"><button type="button" class="close" @click="addOpen = false">×</button><p class="eyebrow">ADD AD ACCOUNT</p><h2>AD 계정 추가</h2><label>AD 계정명<input v-model="addAccount" maxlength="120" autofocus placeholder="예: hong.gildong" /></label><label>부여 권한<select v-model="addRole"><option v-for="role in roles" :key="role.key" :value="role.key">{{ role.label }}</option></select></label><div class="form-actions"><button type="button" class="ghost" @click="addOpen = false">취소</button><button class="primary">추가</button></div></form></div>
  <div v-if="changeOpen" class="modal-backdrop" @click.self="changeOpen = false"><form class="access-modal" @submit.prevent="updateRole"><button type="button" class="close" @click="changeOpen = false">×</button><p class="eyebrow">CHANGE ACCESS ROLE</p><h2>권한 변경</h2><label>AD 계정명<input :value="changing?.ad_account" disabled /></label><label>변경할 권한<select v-model="changeRole"><option v-for="role in roles" :key="role.key" :value="role.key">{{ role.label }}</option></select></label><div class="form-actions"><button type="button" class="ghost" @click="changeOpen = false">취소</button><button class="primary">변경 저장</button></div></form></div>
</template>

<style scoped>
.permission-wrap{max-width:1260px;margin:0 auto;padding:48px 28px 72px}.permission-guide{display:flex;gap:10px;align-items:center;margin-bottom:18px;padding:12px 14px;border:1px solid #dce6fb;border-radius:10px;background:#f5f8ff;color:#65779f;font-size:12px}.permission-guide b{color:#4865ad}.permission-guide code{padding:2px 4px;border-radius:4px;background:#e6edfc;color:#3d5baf}.role-tabs{display:flex;gap:8px;border-bottom:1px solid #e5eaf3;padding-bottom:14px}.role-tabs button{border:1px solid #dfe5ef;border-radius:8px;padding:9px 12px;background:#fff;color:#6e7c91;font:600 12px 'Noto Sans KR';cursor:pointer}.role-tabs button.active{border-color:#6f88ce;background:#eef3ff;color:#4865af}.role-tabs small{margin-left:3px;color:#9aa5b8}.account-panel{margin-top:20px;border:1px solid #e5eaf3;border-radius:14px;overflow:hidden;background:#fff}.panel-head{display:flex;justify-content:space-between;align-items:center;padding:18px 20px}.panel-head div{display:grid;gap:3px}.panel-head b{font-size:14px}.panel-head span{color:#8490a3;font-size:11px}.bulk-delete,.change-btn{border:0;border-radius:7px;padding:8px 10px;font:600 11px 'Noto Sans KR';cursor:pointer}.bulk-delete{background:#fff0f1;color:#c74b5c}.bulk-delete:disabled{opacity:.4;cursor:default}.account-head,.account-row{display:grid;grid-template-columns:48px 1fr 140px 105px;align-items:center;padding:13px 20px;border-top:1px solid #edf0f5}.account-head{background:#f7f9fc;color:#8490a5;font-size:11px}.account-row b{font-size:13px}.account-row time{color:#8995a7;font-size:11px}.change-btn{background:#e9effd;color:#4965b2}.empty-list{margin:0 20px 20px;padding:45px;border:1px dashed #d9e0ea;border-radius:9px;text-align:center;color:#8b97aa;font-size:13px}.access-modal{position:relative;width:min(420px,100%);padding:34px;border-radius:16px;background:#fff;box-shadow:0 25px 70px #1f315a55}.access-modal h2{margin:0;font-size:22px}.access-modal label{display:grid;gap:7px;margin-top:18px;color:#53637d;font-size:12px;font-weight:600}.access-modal input,.access-modal select{border:1px solid #dce3ee;border-radius:8px;padding:11px 12px;background:#fff;font:14px 'Noto Sans KR';outline-color:#6682ce}.access-modal input:disabled{color:#8a96a9;background:#f6f8fb}@media(max-width:760px){.permission-wrap{padding:28px 18px 50px}.role-tabs{overflow:auto}.account-head,.account-row{grid-template-columns:34px 1fr 80px}.account-head span:last-child,.account-row .change-btn{grid-column:3}.account-row time{display:none}.permission-guide{align-items:flex-start;flex-direction:column}}
</style>
