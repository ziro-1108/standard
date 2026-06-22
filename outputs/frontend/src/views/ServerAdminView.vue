<script setup>
import { onMounted, ref } from 'vue'
import { api, session } from '../api'

const announcements = ref([])
const title = ref('')
const content = ref('')
const publishNow = ref(true)
const error = ref('')
const saving = ref(false)

async function load() {
  try { announcements.value = await api('/admin/announcements') }
  catch (e) { error.value = e.message }
}

async function submit() {
  if (!title.value.trim() || !content.value.trim()) { error.value = '공지 제목과 내용을 입력해 주세요.'; return }
  saving.value = true
  try {
    await api('/admin/announcements', { method: 'POST', body: JSON.stringify({ title: title.value, content: content.value, is_published: publishNow.value }) })
    title.value = ''; content.value = ''; publishNow.value = true; error.value = ''; await load()
  } catch (e) { error.value = e.message }
  finally { saving.value = false }
}

async function toggle(announcement) {
  try {
    await api(`/admin/announcements/${announcement.id}`, { method: 'PATCH', body: JSON.stringify({ is_published: !announcement.is_published }) })
    await load()
  } catch (e) { error.value = e.message }
}

async function remove(announcement) {
  if (!window.confirm(`'${announcement.title}' 공지를 영구 삭제할까요?`)) return
  try {
    await api(`/admin/announcements/${announcement.id}`, { method: 'DELETE' })
    await load()
  } catch (e) { error.value = e.message }
}

onMounted(load)
</script>

<template>
  <section class="admin-wrap">
    <header class="page-intro"><div><p class="eyebrow">SERVER CONSOLE</p><h1>공지 관리</h1><p>홈 화면 로그인 시 사용자에게 보여 줄 공지를 작성하고 게시 상태를 관리합니다.</p></div><span class="admin-badge">{{ session.user?.username }} · 서버 관리자</span></header>
    <div v-if="error" class="error-banner">{{ error }}</div>
    <div class="admin-grid">
      <form class="announcement-form" @submit.prevent="submit"><p class="form-title">새 공지 작성</p><label>공지 제목<input v-model="title" maxlength="200" placeholder="예: 분석 표준 시스템 정기 점검 안내" /></label><label>공지 내용<textarea v-model="content" maxlength="4000" placeholder="사용자에게 안내할 내용을 입력하세요."></textarea></label><label class="publish-check"><input v-model="publishNow" type="checkbox" /> 작성 즉시 게시</label><button class="primary" :disabled="saving">{{ saving ? '등록 중…' : '공지 등록' }}</button></form>
      <div class="announcement-list"><div class="list-header"><p class="form-title">공지 목록</p><span>{{ announcements.length }}건</span></div><div v-if="announcements.length" class="items"><article v-for="announcement in announcements" :key="announcement.id" class="announcement-item"><div class="announcement-meta"><span :class="announcement.is_published ? 'published' : 'hidden'">{{ announcement.is_published ? '게시 중' : '내림' }}</span><time>{{ new Date(announcement.created_at).toLocaleDateString('ko-KR') }}</time></div><h3>{{ announcement.title }}</h3><p>{{ announcement.content }}</p><div class="notice-actions"><button :class="announcement.is_published ? 'unpublish' : 'publish'" @click="toggle(announcement)">{{ announcement.is_published ? '공지 내리기' : '다시 게시' }}</button><button class="delete" @click="remove(announcement)">삭제</button></div></article></div><div v-else class="no-notice">작성된 공지가 없습니다.</div></div>
    </div>
  </section>
</template>

<style scoped>
.admin-wrap { max-width: 1260px; margin: 0 auto; padding: 48px 28px 72px; }
.admin-badge { border-radius: 9px; padding: 9px 12px; background: #edf2ff; color: #536db4; font-size: 12px; font-weight: 600; }
.admin-grid { display: grid; grid-template-columns: minmax(300px, .85fr) minmax(380px, 1.4fr); gap: 22px; align-items: start; }
.announcement-form, .announcement-list { background: #fff; border: 1px solid #e5eaf3; border-radius: 14px; padding: 23px; }
.form-title { margin: 0; font-weight: 700; font-size: 16px; color: #2c3d5f; }
.announcement-form label { display: grid; gap: 7px; margin-top: 17px; color: #57667f; font-size: 12px; font-weight: 600; }
.announcement-form input:not([type='checkbox']), .announcement-form textarea { width: 100%; border: 1px solid #dce3ee; border-radius: 8px; padding: 10px 11px; color: #293955; font: 13px 'Noto Sans KR'; resize: vertical; outline-color: #6682ce; }
.announcement-form textarea { min-height: 155px; line-height: 1.65; }.announcement-form .publish-check { display: flex; align-items: center; gap: 8px; color: #65758f; }.announcement-form .primary { width: 100%; margin-top: 20px; }
.list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }.list-header span { color: #8390a5; font-size: 12px; }.items { display: grid; gap: 10px; }.announcement-item { position: relative; border: 1px solid #e9edf4; border-radius: 10px; padding: 16px 17px; }.announcement-item h3 { margin: 8px 0 5px; font-size: 14px; }.announcement-item p { margin: 0 0 13px; color: #6d7a8e; white-space: pre-wrap; font-size: 12px; line-height: 1.6; }.announcement-meta { display: flex; gap: 8px; align-items: center; }.announcement-meta span { border-radius: 5px; padding: 3px 6px; font-size: 10px; font-weight: 600; }.published { background: #e6f7ef; color: #319b71; }.hidden { background: #f1f3f6; color: #7b8798; }.announcement-meta time { color: #98a2b2; font-size: 10px; }.notice-actions { display: flex; gap: 7px; }.announcement-item button { border: 0; border-radius: 7px; padding: 7px 9px; font: 600 11px 'Noto Sans KR'; cursor: pointer; }.unpublish { background: #fff0f1; color: #c74b5c; }.publish { background: #e9effd; color: #4a66b4; }.delete { background: #f0f2f6; color: #69778d; }.no-notice { border: 1px dashed #d9e0ea; border-radius: 9px; padding: 45px; text-align: center; color: #8b97aa; font-size: 13px; }
@media (max-width: 760px) { .admin-wrap { padding: 28px 18px 50px; }.admin-grid { grid-template-columns: 1fr; }.page-intro { align-items: flex-start; flex-direction: column; gap: 14px; } }
</style>
