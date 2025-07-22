<template>
    <div class="p-4 md:p-8 max-w-4xl mx-auto">
        <!-- Search and filter card -->
        <div class="mb-6 flex flex-col md:flex-row md:items-end md:space-x-4 bg-white shadow-md rounded-lg p-4 md:p-6 w-full transition-all">
            <div class="flex-1 mb-4 md:mb-0">
                <label for="email-search" class="block text-gray-700 font-semibold mb-2">Search by email</label>
                <div class="relative">
                    <input
                        id="email-search"
                        v-model="search"
                        type="text"
                        placeholder="Type email to search..."
                        class="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 border-gray-300 text-lg transition"
                    />
                    <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd" />
                        </svg>
                    </div>
                </div>
            </div>
            <div class="w-full md:w-64">
                <label for="sort-order" class="block text-gray-700 font-semibold mb-2">Sort by</label>
                <select 
                    id="sort-order"
                    v-model="order" 
                    class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 border-gray-300 text-lg transition appearance-none bg-white"
                >
                    <option value="unread_desc">Unread (highest first)</option>
                    <option value="unread_asc">Unread (lowest first)</option>
                    <option value="alpha_asc">Email (A-Z)</option>
                    <option value="alpha_desc">Email (Z-A)</option>
                    <option value="normal">Default order</option>
                </select>
            </div>
        </div>

        <!-- Loading state -->
        <div v-if="loading" class="flex justify-center py-10">
            <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>

        <!-- Error state -->
        <div v-else-if="error" class="bg-red-50 border-l-4 border-red-500 p-4 rounded-md my-4">
            <div class="flex">
                <div class="flex-shrink-0 text-red-500">
                    <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                    </svg>
                </div>
                <div class="ml-3">
                    <p class="text-sm text-red-700">Failed to load dialogs. Please try again.</p>
                </div>
            </div>
        </div>

        <!-- Dialogs list -->
        <transition-group name="list" tag="ul" class="space-y-3" v-else>
            <li
                v-for="dialog in filteredDialogs"
                :key="dialog.id"
                class="flex items-center justify-between bg-white shadow-sm rounded-lg px-6 py-4 cursor-pointer hover:bg-blue-50 transition-all duration-200 border border-gray-200"
                :class="{'border-l-4 border-l-blue-500': dialog.unreadCount > 0}"
                @click="goToDialog(dialog.id)"
            >
                <div class="flex flex-col">
                    <span class="font-medium text-gray-900 text-lg" v-html="highlightMatch(dialog.email)"></span>
                    <span class="text-gray-500 text-sm">Last message: {{ formatDate(new Date()) }}</span>
                </div>
                <span
                    v-if="dialog.unreadCount > 0"
                    class="bg-blue-500 text-white text-xs font-bold px-3 py-1 rounded-full shadow-sm"
                >
                    {{ dialog.unreadCount }}
                </span>
            </li>
            
            <!-- Empty state -->
            <li v-if="filteredDialogs.length === 0 && !loading" key="empty" class="text-center p-8 bg-gray-50 rounded-lg border border-dashed border-gray-300">
                <svg class="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                </svg>
                <p class="text-gray-500 text-lg">No dialogs found</p>
                <p class="text-gray-400 mt-1">Try adjusting your search criteria</p>
            </li>
        </transition-group>
    </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'

const dialogs = ref([])
const search = ref('')
const order = ref('unread_desc')
const loading = ref(false)
const error = ref(null)
const router = useRouter()

// Debounced search
const debouncedSearch = ref('')
let debounceTimer = null
watch(search, (newValue) => {
    clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => {
        debouncedSearch.value = newValue
    }, 300)
})

async function fetchDialogs() {
    loading.value = true
    error.value = null
    
    try {
        dialogs.value = await fakeFetchDialogs()
    } catch (err) {
        error.value = err.message || 'Failed to load dialogs'
        console.error('Error fetching dialogs:', err)
    } finally {
        loading.value = false
    }
}

function fakeFetchDialogs() {
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            // Simulate a 10% chance of error for testing
            if (Math.random() < 0.1) {
                reject(new Error('Network error'))
                return
            }
            
            resolve([
                { id: 1, email: 'alice@example.com', unreadCount: 2 },
                { id: 2, email: 'bob@example.com', unreadCount: 0 },
                { id: 3, email: 'carol@example.com', unreadCount: 5 },
                { id: 4, email: 'dave@example.com', unreadCount: 1 },
                { id: 5, email: 'support@example.com', unreadCount: 3 },
            ])
        }, 800)
    })
}

onMounted(() => {
    fetchDialogs()
})

const filteredDialogs = computed(() => {
    let result = dialogs.value
    
    if (debouncedSearch.value) {
        result = result.filter(dialog =>
            dialog.email.toLowerCase().includes(debouncedSearch.value.toLowerCase())
        )
    }
    
    switch (order.value) {
        case 'unread_desc':
            return [...result].sort((a, b) => b.unreadCount - a.unreadCount)
        case 'unread_asc':
            return [...result].sort((a, b) => a.unreadCount - b.unreadCount)
        case 'alpha_asc':
            return [...result].sort((a, b) => a.email.localeCompare(b.email))
        case 'alpha_desc':
            return [...result].sort((a, b) => b.email.localeCompare(a.email))
        default:
            return result
    }
})

function goToDialog(id) {
    router.push(`/dialogs/${id}`)
}

function highlightMatch(email) {
    if (!debouncedSearch.value) return email
    const escaped = debouncedSearch.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const regex = new RegExp(escaped, 'gi')
    return email.replace(regex, match => `<mark class="bg-yellow-200 rounded px-1">${match}</mark>`)
}

function formatDate(date) {
    return new Intl.DateTimeFormat('en-US', { 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date)
}
</script>

<style scoped>
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}
.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>