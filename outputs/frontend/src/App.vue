<script setup>
import { computed, ref } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { session, signIn, signOut } from './api'

const route = useRoute()
const open = ref(false)
const username = ref('viewer')
const password = ref('demo1234')
const error = ref('')
const roleName = computed(() => ({
  viewer: '일반 유저', engineer: '내부 관리자', executive: '고위 관리자', server_admin: '서버 관리자',
})[session.user?.role])
const isServerAdmin = computed(() => session.user?.role === 'server_admin')
const canUseMyPage = computed(() => ['engineer', 'executive'].includes(session.user?.role))

async function login() {
  try { await signIn(username.value, password.value); open.value = false; error.value = ''; location.assign('/') }
  catch (e) { error.value = e.message }
}
</script>

<template>
  <div class="app-shell">
    <header class="header">
      <RouterLink to="/" class="brand"><span class="brand-mark">A</span><span>제품명 <b>관리 페이지</b></span></RouterLink>
      <div class="account" v-if="session.user"><span class="role-dot"></span><span>{{ session.user.username }} · {{ roleName }}</span><button class="ghost" @click="signOut(); $router.push('/')">로그아웃</button></div>
      <button v-else class="login-trigger" @click="open = true">로그인</button>
    </header>
    <nav class="nav">
      <RouterLink to="/" :class="{ active: route.path === '/' }">홈페이지</RouterLink>
      <RouterLink to="/standards" :class="{ active: route.path === '/standards' }">분석 표준</RouterLink>
      <RouterLink v-if="canUseMyPage" to="/my-page" :class="{ active: route.path === '/my-page' }">마이페이지</RouterLink>
      <RouterLink v-if="isServerAdmin" to="/notice-admin" :class="{ active: route.path === '/notice-admin' }">공지 관리</RouterLink>
      <RouterLink v-if="isServerAdmin" to="/product-admin" :class="{ active: route.path === '/product-admin' }">제품 관리</RouterLink>
      <RouterLink v-if="isServerAdmin" to="/server-admin" :class="{ active: route.path === '/server-admin' }">서버 관리</RouterLink>
      <RouterLink v-if="isServerAdmin" to="/permission-admin" :class="{ active: route.path === '/permission-admin' }">권한 관리</RouterLink>
    </nav>
    <main><RouterView /></main>
    <footer><span>분석팀 <b>부서1</b> 박선재</span><span>Analysis Standard Management · {{ new Date().getFullYear() }}</span></footer>
  </div>
  <div v-if="open" class="modal-backdrop" @click.self="open = false"><form class="login-modal" @submit.prevent="login"><button type="button" class="close" @click="open = false">×</button><p class="eyebrow">WELCOME BACK</p><h2>업무 공간에 로그인</h2><p class="muted">권한에 맞는 표준 관리 기능을 이용할 수 있습니다.</p><label>계정<input v-model="username" /></label><label>비밀번호<input v-model="password" type="password" /></label><p v-if="error" class="error">{{ error }}</p><button class="primary">로그인</button><small>데모: viewer / engineer / executive / server_admin · demo1234</small></form></div>
</template>
