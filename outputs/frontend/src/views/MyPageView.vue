<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

const summary = ref(null)
const error = ref('')
const roleName = computed(() => ({ engineer: '내부 엔지니어', executive: '고위 관리자' })[summary.value?.role] || '')
const stageLabel = { 시료제작1: '시료제작 1', 시료제작2: '시료제작 2', 시료제작3: '시료제작 3', 촬영: '촬영', 측정: '측정' }
onMounted(async () => { try { summary.value = await api('/my-page') } catch (e) { error.value = '마이페이지는 내부 엔지니어와 고위 관리자만 이용할 수 있습니다.' } })
</script>

<template>
  <section class="mypage-wrap"><header class="page-intro"><div><p class="eyebrow">MY WORKSPACE</p><h1>마이페이지</h1><p>내 직급과 분석 표준 등록 현황을 한 눈에 확인하세요.</p></div></header><div v-if="error" class="error-banner">{{ error }}</div><template v-else-if="summary"><div class="profile-card"><div class="profile-mark">{{ summary.username.slice(0, 1).toUpperCase() }}</div><div><p>로그인 계정</p><h2>{{ summary.username }}</h2><span>{{ roleName }}</span></div><strong><em>{{ summary.total_documents }}</em>개<br /><small>등록된 하위 분석 표준</small></strong></div><div class="stage-summary"><article v-for="(count, stage) in summary.stage_counts" :key="stage"><span>{{ stageLabel[stage] || stage }}</span><b>{{ count }}<small>개</small></b><div class="meter"><i :style="{ width: `${summary.total_documents ? Math.max(8, count / summary.total_documents * 100) : 0}%` }"></i></div></article></div></template></section>
</template>

<style scoped>
.mypage-wrap{max-width:1040px;margin:0 auto;padding:48px 28px 72px}.profile-card{display:flex;align-items:center;gap:17px;padding:28px 32px;border-radius:16px;background:linear-gradient(120deg,#f0f4ff,#fafbfe);border:1px solid #dee7fa}.profile-mark{display:grid;place-items:center;width:55px;height:55px;border-radius:16px;background:#627dc6;color:#fff;font:600 24px Outfit}.profile-card p{margin:0;color:#77869f;font-size:12px}.profile-card h2{margin:3px 0;font-size:21px}.profile-card span{color:#526db3;font-size:12px;font-weight:600}.profile-card strong{margin-left:auto;color:#536eae;text-align:right;font:500 14px 'Noto Sans KR'}.profile-card em{font:600 32px Outfit;font-style:normal}.profile-card small{color:#8592a5;font-size:11px;font-weight:400}.stage-summary{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-top:24px}.stage-summary article{padding:18px;border:1px solid #e5eaf3;border-radius:13px;background:#fff}.stage-summary span{display:block;color:#758399;font-size:12px}.stage-summary b{display:block;margin:10px 0;color:#344c88;font:600 27px Outfit}.stage-summary b small{margin-left:2px;color:#8b97a9;font:500 11px 'Noto Sans KR'}.meter{height:5px;overflow:hidden;border-radius:6px;background:#edf1f7}.meter i{display:block;height:100%;border-radius:6px;background:#7892d8}@media(max-width:760px){.mypage-wrap{padding:28px 18px 50px}.profile-card{padding:22px;flex-wrap:wrap}.profile-card strong{margin-left:0;text-align:left;width:100%}.stage-summary{grid-template-columns:repeat(2,1fr)}}
</style>
