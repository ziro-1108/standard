<script setup>
import { computed, onMounted, ref } from 'vue'
import { api, session } from '../api'

const data = ref(null)
const error = ref('')
const slide = ref(0)
const announcements = ref([])
const announcementIndex = ref(0)
const announcementsOpen = ref(false)
const homeImages = ref([])
const slides = [
  { kicker: 'STANDARDIZE WITH CLARITY', title: '분석의 흐름을\n한 곳에서 관리하세요.', text: '제품별 분석 표준을 단계별로 정리하고 최신 문서를 빠르게 확인합니다.', tone: 'blue' },
  { kicker: 'ALWAYS IN STEP', title: '제작부터 측정까지,\n끊기지 않는 기준.', text: '업로드 시점과 문서 상태를 한 눈에 확인해 팀의 다음 작업을 또렷하게 만듭니다.', tone: 'lavender' },
  { kicker: 'A QUIET CONTROL ROOM', title: '필요한 권한으로\n안전하게 협업합니다.', text: '열람, 업로드, S/U 완료 처리를 권한에 따라 명확히 나눕니다.', tone: 'coral' },
]
const currentAnnouncement = computed(() => announcements.value[announcementIndex.value])

function nextAnnouncement() { announcementIndex.value = (announcementIndex.value + 1) % announcements.value.length }
function previousAnnouncement() { announcementIndex.value = (announcementIndex.value - 1 + announcements.value.length) % announcements.value.length }

onMounted(async () => {
  if (!session.user) { error.value = '로그인 후 등록 현황을 확인할 수 있습니다.'; return }
  try {
    const [dashboard, noticeList, images] = await Promise.all([api('/dashboard'), api('/announcements'), api('/home-images')])
    data.value = dashboard
    announcements.value = noticeList
    homeImages.value = images
    announcementsOpen.value = noticeList.length > 0
  } catch (e) { error.value = e.message }
})
</script>

<template>
  <section class="home-wrap">
    <div class="hero" :class="slides[slide % slides.length].tone"><img v-if="homeImages[slide]" class="managed-home-image" :src="homeImages[slide].image_url" :alt="`홈 슬라이더 ${slide + 1}`" /><div class="hero-content"><p class="eyebrow">{{ slides[slide % slides.length].kicker }}</p><h1>{{ slides[slide % slides.length].title }}</h1><p>{{ slides[slide % slides.length].text }}</p><RouterLink to="/standards" class="hero-link">표준 살펴보기 <span>→</span></RouterLink></div><div v-if="!homeImages[slide]" class="hero-art"><div class="orb one"></div><div class="orb two"></div><div class="paper-card"><span class="mini-label">ANALYSIS FLOW</span><div class="flow-line"><i></i><i></i><i></i><i></i><i></i></div><div class="paper-bars"><b></b><b></b><b></b></div></div></div><div class="slider-nav"><button v-for="(_, i) in (homeImages.length || slides)" :key="i" :class="{ picked: slide === i }" @click="slide = i"></button></div></div>
    <div class="summary-section"><div><p class="eyebrow">CURRENT OVERVIEW</p><h2>등록 현황</h2><p class="muted">분석 표준과 하위 표준의 누적 등록 수입니다.</p></div><div v-if="data" class="counts"><div class="count-card"><strong>{{ data.purpose_count }}</strong><span>분석 표준</span></div><div class="count-card accent"><strong>{{ data.document_count }}</strong><span>하위 표준 문서</span></div></div></div>
    <div v-if="data" class="stage-table"><div class="table-head"><span>하위 분석 표준</span><span>등록 수</span></div><div v-for="(count, stage) in data.stage_counts" :key="stage" class="table-row"><span>{{ stage }}</span><b>{{ count }}<em>개</em></b></div></div><div v-else class="notice">{{ error }}</div>
  </section>

  <div v-if="announcementsOpen && currentAnnouncement" class="notice-backdrop" @click.self="announcementsOpen = false">
    <section class="announcement-modal"><button class="close" @click="announcementsOpen = false">×</button><p class="eyebrow">NOTICE · {{ announcementIndex + 1 }} / {{ announcements.length }}</p><h2>{{ currentAnnouncement.title }}</h2><p class="announcement-content">{{ currentAnnouncement.content }}</p><div class="announcement-footer"><button class="notice-nav" :disabled="announcements.length < 2" @click="previousAnnouncement">← 이전</button><button class="notice-nav" :disabled="announcements.length < 2" @click="nextAnnouncement">다음 →</button></div></section>
  </div>
</template>

<style scoped>
.notice-backdrop { position: fixed; inset: 0; z-index: 20; display: grid; place-items: center; padding: 20px; background: #17253f70; }
.announcement-modal { position: relative; width: min(520px, 100%); border-radius: 18px; padding: 36px; background: #fff; box-shadow: 0 30px 80px #15254a50; }
.announcement-modal h2 { margin: 0 0 17px; font-size: 25px; letter-spacing: -1px; }
.announcement-content { white-space: pre-wrap; margin: 0; color: #53637d; line-height: 1.8; font-size: 14px; }
.announcement-footer { display: flex; justify-content: space-between; gap: 10px; border-top: 1px solid #edf0f5; margin-top: 28px; padding-top: 18px; }
.notice-nav { border: 0; background: #eef3ff; color: #4663b2; border-radius: 8px; padding: 9px 13px; font: 600 12px 'Noto Sans KR'; cursor: pointer; }
.notice-nav:disabled { opacity: .4; cursor: default; }
.managed-home-image { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; opacity: .72; }.managed-home-image + .hero-content { text-shadow: 0 2px 18px #17253f77; }
</style>
