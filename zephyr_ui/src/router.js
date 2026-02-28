import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    name: "Chat",
    component: () => import("./views/ChatView.vue"),
  },
  {
    path: "/dashboard",
    name: "Dashboard",
    component: () => import("./views/DashboardView.vue"),
  },
];

export default createRouter({
  history: createWebHistory(),
  routes,
});
