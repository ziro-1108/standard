import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import HomeView from './views/HomeView.vue'
import StandardsView from './views/StandardsView.vue'
import ServerAdminView from './views/ServerAdminView.vue'
import ProductAdminView from './views/ProductAdminView.vue'
import ServerManagementView from './views/ServerManagementView.vue'
import MyPageView from './views/MyPageView.vue'
import PermissionAdminView from './views/PermissionAdminView.vue'
import './style.css'

const router = createRouter({ history: createWebHistory(), routes: [
  { path: '/', component: HomeView }, { path: '/standards', component: StandardsView }, { path: '/my-page', component: MyPageView }, { path: '/notice-admin', component: ServerAdminView }, { path: '/product-admin', component: ProductAdminView }, { path: '/server-admin', component: ServerManagementView }, { path: '/permission-admin', component: PermissionAdminView }
] })
createApp(App).use(router).mount('#app')
