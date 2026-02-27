import { defineStore } from "pinia";
import { ref } from "vue";

export const useThemeStore = defineStore("theme", () => {
  const isDark = ref(true);

  function toggle() {
    isDark.value = !isDark.value;
    document.documentElement.classList.toggle("dark", isDark.value);
    document.documentElement.classList.toggle("light", !isDark.value);
  }

  function init() {
    const pref = localStorage.getItem("astrafox-theme");
    if (pref === "light") {
      isDark.value = false;
      document.documentElement.classList.remove("dark");
      document.documentElement.classList.add("light");
    }
  }

  function save() {
    localStorage.setItem("astrafox-theme", isDark.value ? "dark" : "light");
  }

  return { isDark, toggle, init, save };
});
