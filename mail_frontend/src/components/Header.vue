<template>
    <header class="bg-slate-100 shadow-md px-4 py-2 flex items-center justify-between">
        <!-- Logo and Home Link -->
        <router-link :to="{ name: 'home' }" class="flex items-center space-x-2">
            <img src="/ico.svg" alt="Logo" class="h-8 w-8" />
            <span class="font-bold text-lg hidden sm:inline">MailApp</span>
        </router-link>

        <!-- Desktop Navigation -->
        <nav class="hidden md:flex items-center space-x-6">
            <router-link :to="{ name: 'dialogs' }" class="text-gray-700 hover:text-blue-600 font-medium">
                Dialogs
            </router-link>
            <router-link :to="{ name: 'settings' }" class="text-gray-700 hover:text-blue-600 font-medium">
                Settings
            </router-link>
        </nav>

        <!-- Mobile Burger -->
        <button @click="menuOpen = !menuOpen" class="md:hidden focus:outline-none">
            <svg class="h-6 w-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M4 6h16M4 12h16M4 18h16" />
            </svg>
        </button>

        <!-- Mobile Menu -->
        <transition name="fade">
            <div v-if="menuOpen" class="absolute top-14 left-0 w-full bg-slate-100 shadow-md md:hidden z-50">
                <nav class="flex flex-col items-start px-4 py-2 space-y-2">
                    <router-link :to="{ name: 'home' }" class="w-full py-2 text-gray-700 hover:text-blue-600 font-medium" @click="menuOpen = false">
                        Home
                    </router-link>
                    <router-link :to="{ name: 'dialogs' }" class="w-full py-2 text-gray-700 hover:text-blue-600 font-medium" @click="menuOpen = false">
                        Dialogs
                    </router-link>
                    <router-link :to="{ name: 'settings' }" class="w-full py-2 text-gray-700 hover:text-blue-600 font-medium" @click="menuOpen = false">
                        Settings
                    </router-link>
                </nav>
            </div>
        </transition>
    </header>
</template>

<script setup>
import { ref } from 'vue'
const menuOpen = ref(false)
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
    transition: opacity 0.2s;
}
.fade-enter-from, .fade-leave-to {
    opacity: 0;
}
</style>