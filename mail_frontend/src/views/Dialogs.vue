<template>
    <div class="p-4 md:p-8 max-w-4xl mx-auto">
        <!-- Header with stats -->
        <div class="mb-4 flex justify-between items-center">
            <h1 class="text-2xl font-bold text-gray-800">Conversations</h1>
            <div class="flex items-center space-x-2">
                <span class="text-sm text-gray-600">{{ filteredDialogs.length }} conversations</span>
                <button @click="refreshDialogs" class="p-2 rounded-full hover:bg-gray-100" title="Refresh">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" :class="{ 'animate-spin': loading }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                </button>
            </div>
        </div>

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
                        @keydown.enter="onEnterPress"
                        @keydown.down="onArrowDown"
                        @keydown.up="onArrowUp"
                    />
                    <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd" />
                        </svg>
                    </div>
                    <button 
                        v-if="search" 
                        @click="search = ''" 
                        class="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-500 hover:text-gray-700"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                        </svg>
                    </button>
                </div>
            </div>
            <div class="w-full md:w-64">
                <label for="sort-order" class="block text-gray-700 font-semibold mb-2">Sort by</label>
                <div class="relative">
                    <select 
                        id="sort-order"
                        v-model="order" 
                        class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 border-gray-300 text-lg transition appearance-none bg-white"
                    >
                        <option value="latest">Latest message</option>
                        <option value="unread_desc">Unread (highest first)</option>
                        <option value="unread_asc">Unread (lowest first)</option>
                        <option value="alpha_asc">Email (A-Z)</option>
                        <option value="alpha_desc">Email (Z-A)</option>
                    </select>
                    <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
                        <svg class="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                            <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                        </svg>
                    </div>
                </div>
            </div>
        </div>

        <!-- Error state -->
        <div v-if="error" class="bg-red-50 border-l-4 border-red-500 p-4 rounded-md my-4">
            <div class="flex">
                <div class="flex-shrink-0 text-red-500">
                    <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                    </svg>
                </div>
                <div class="ml-3 flex justify-between w-full items-center">
                    <p class="text-sm text-red-700">Failed to load dialogs. Please try again.</p>
                    <button @click="fetchDialogs" class="text-sm text-red-700 underline">Retry</button>
                </div>
            </div>
        </div>

        <!-- Loading skeleton -->
        <div v-if="loading && !dialogs.length" aria-live="polite" aria-busy="true">
            <div v-for="i in 5" :key="i" class="animate-pulse bg-white shadow-sm rounded-lg px-6 py-4 mb-3 border border-gray-200">
                <div class="flex justify-between">
                    <div class="w-1/3 h-4 bg-gray-200 rounded"></div>
                    <div class="w-8 h-8 bg-gray-200 rounded-full"></div>
                </div>
                <div class="w-1/2 h-3 bg-gray-200 rounded mt-3"></div>
            </div>
        </div>

        <!-- Dialogs list -->
        <div v-else>
            <transition-group name="list" tag="ul" class="space-y-3" role="list" aria-label="Conversations">
                <li
                    v-for="(dialog, index) in filteredDialogs"
                    :key="dialog.id"
                    class="flex items-center justify-between bg-white shadow-sm rounded-lg px-6 py-4 cursor-pointer hover:bg-blue-50 transition-all duration-200 border border-gray-200"
                    :class="{
                        'border-l-4 border-l-blue-500': dialog.unreadCount > 0,
                        'bg-blue-50': selectedIndex === index
                    }"
                    @click="goToDialog(dialog.id)"
                    tabindex="0"
                    :ref="el => { if (selectedIndex === index) selectedElement = el }"
                    role="listitem"
                >
                    <div class="flex flex-col flex-grow mr-4">
                        <div class="flex items-center justify-between">
                            <span class="font-medium text-gray-900 text-lg" v-html="highlightMatch(dialog.email)"></span>
                            <span class="text-xs text-gray-500">{{ formatDate(dialog.lastMessageDate || new Date()) }}</span>
                        </div>
                        <p class="text-gray-600 text-sm mt-1 line-clamp-1">
                            {{ dialog.lastMessage || 'No messages yet' }}
                        </p>
                    </div>
                    <div class="flex items-center space-x-2">
                        <button 
                            v-if="dialog.unreadCount > 0" 
                            @click.stop="markAsRead(dialog.id)"
                            class="text-gray-500 hover:text-blue-500 focus:outline-none p-1"
                            title="Mark as read"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                            </svg>
                        </button>
                        <span
                            v-if="dialog.unreadCount > 0"
                            class="bg-blue-500 text-white text-xs font-bold px-3 py-1 rounded-full shadow-sm"
                            aria-label="Unread messages"
                        >
                            {{ dialog.unreadCount }}
                        </span>
                    </div>
                </li>
                
                <!-- Empty state -->
                <li v-if="filteredDialogs.length === 0 && !loading" key="empty" class="text-center p-8 bg-gray-50 rounded-lg border border-dashed border-gray-300">
                    <svg class="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                    </svg>
                    <p class="text-gray-500 text-lg">No conversations found</p>
                    <p class="text-gray-400 mt-1 mb-4">{{ search ? 'Try adjusting your search criteria' : 'Start a new conversation' }}</p>
                    <button v-if="!search" class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition">
                        Start new conversation
                    </button>
                </li>
            </transition-group>
            
            <!-- Pagination -->
            <div v-if="filteredDialogs.length > 0" class="mt-6 flex justify-between items-center">
                <span class="text-sm text-gray-600">Showing {{ filteredDialogs.length }} results</span>
                <button v-if="hasMoreDialogs" @click="loadMore" class="text-blue-500 hover:text-blue-700 flex items-center">
                    Load more
                    <svg v-if="loadingMore" class="ml-2 animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'

const dialogs = ref([])
const search = ref('')
const order = ref('latest')
const loading = ref(false)
const loadingMore = ref(false)
const error = ref(null)
const router = useRouter()
const selectedIndex = ref(-1)
const selectedElement = ref(null)
const limit = ref(10)
const hasMoreDialogs = ref(true)

// Debounced search
const debouncedSearch = ref('')
let debounceTimer = null
watch(search, (newValue) => {
        clearTimeout(debounceTimer)
        debounceTimer = setTimeout(() => {
                debouncedSearch.value = newValue
                selectedIndex.value = -1
        }, 300)
})

// Reset selection when order changes
watch(order, () => {
        selectedIndex.value = -1
})

async function fetchDialogs() {
        loading.value = true
        error.value = null
        
        try {
                // Simulating API call with localStorage caching
                const cachedData = localStorage.getItem('dialogsCache')
                if (cachedData) {
                        dialogs.value = JSON.parse(cachedData)
                }
                
                const newData = await fakeFetchDialogs()
                dialogs.value = newData
                
                // Cache the result
                localStorage.setItem('dialogsCache', JSON.stringify(newData))
        } catch (err) {
                error.value = err.message || 'Failed to load dialogs'
                console.error('Error fetching dialogs:', err)
        } finally {
                loading.value = false
        }
}

function refreshDialogs() {
        // Clear cache and fetch fresh data
        localStorage.removeItem('dialogsCache')
        fetchDialogs()
}

async function loadMore() {
        if (loadingMore.value) return
        
        loadingMore.value = true
        try {
                const moreDialogs = await fakeFetchMoreDialogs()
                if (moreDialogs.length === 0) {
                        hasMoreDialogs.value = false
                } else {
                        dialogs.value = [...dialogs.value, ...moreDialogs]
                }
        } catch (err) {
                console.error('Error loading more dialogs:', err)
        } finally {
                loadingMore.value = false
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
                                { 
                                        id: 1, 
                                        email: 'alice@example.com', 
                                        unreadCount: 2, 
                                        lastMessage: 'Could you please review the latest proposal?',
                                        lastMessageDate: new Date(Date.now() - 1000 * 60 * 30) // 30 minutes ago
                                },
                                { 
                                        id: 2, 
                                        email: 'bob@example.com', 
                                        unreadCount: 0,
                                        lastMessage: 'Thanks for your help with the project!',
                                        lastMessageDate: new Date(Date.now() - 1000 * 60 * 60 * 3) // 3 hours ago
                                },
                                { 
                                        id: 3, 
                                        email: 'carol@example.com', 
                                        unreadCount: 5,
                                        lastMessage: 'We need to discuss the timeline for the next sprint',
                                        lastMessageDate: new Date(Date.now() - 1000 * 60 * 15) // 15 minutes ago
                                },
                                { 
                                        id: 4, 
                                        email: 'dave@example.com', 
                                        unreadCount: 1,
                                        lastMessage: 'Did you get my email about the client meeting?',
                                        lastMessageDate: new Date(Date.now() - 1000 * 60 * 60 * 24) // 1 day ago
                                },
                                { 
                                        id: 5, 
                                        email: 'support@example.com', 
                                        unreadCount: 3,
                                        lastMessage: 'Your ticket #45678 has been updated',
                                        lastMessageDate: new Date(Date.now() - 1000 * 60 * 5) // 5 minutes ago
                                },
                        ])
                }, 800)
        })
}

function fakeFetchMoreDialogs() {
        return new Promise((resolve) => {
                setTimeout(() => {
                        resolve([
                                { 
                                        id: 6, 
                                        email: 'marketing@example.com', 
                                        unreadCount: 0,
                                        lastMessage: 'New campaign materials are ready for review',
                                        lastMessageDate: new Date(Date.now() - 1000 * 60 * 60 * 48) // 2 days ago
                                },
                                { 
                                        id: 7, 
                                        email: 'hr@example.com', 
                                        unreadCount: 2,
                                        lastMessage: 'Please complete your annual review by Friday',
                                        lastMessageDate: new Date(Date.now() - 1000 * 60 * 60 * 12) // 12 hours ago
                                }
                        ])
                }, 800)
        })
}

function markAsRead(id) {
        const dialog = dialogs.value.find(d => d.id === id)
        if (dialog) {
                dialog.unreadCount = 0
        }
}

onMounted(() => {
        fetchDialogs()
        
        // Add global keyboard handler
        window.addEventListener('keydown', handleGlobalKeydown)
})

onUnmounted(() => {
        window.removeEventListener('keydown', handleGlobalKeydown)
})

function handleGlobalKeydown(e) {
        // Add global shortcuts if needed
        if (e.key === 'r' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault()
                refreshDialogs()
        }
}

function onEnterPress() {
        if (selectedIndex.value >= 0 && selectedIndex.value < filteredDialogs.value.length) {
                goToDialog(filteredDialogs.value[selectedIndex.value].id)
        }
}

function onArrowDown() {
        if (selectedIndex.value < filteredDialogs.value.length - 1) {
                selectedIndex.value++
                scrollToSelected()
        }
}

function onArrowUp() {
        if (selectedIndex.value > 0) {
                selectedIndex.value--
                scrollToSelected()
        }
}

function scrollToSelected() {
        nextTick(() => {
                if (selectedElement.value) {
                        selectedElement.value.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
                }
        })
}

const filteredDialogs = computed(() => {
        let result = dialogs.value
        
        if (debouncedSearch.value) {
                result = result.filter(dialog =>
                        dialog.email.toLowerCase().includes(debouncedSearch.value.toLowerCase())
                )
        }
        
        switch (order.value) {
                case 'latest':
                        return [...result].sort((a, b) => new Date(b.lastMessageDate) - new Date(a.lastMessageDate))
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
        const now = new Date()
        const messageDate = new Date(date)
        
        // If it's today, show time only
        if (messageDate.toDateString() === now.toDateString()) {
                return new Intl.DateTimeFormat('en-US', { 
                        hour: 'numeric', 
                        minute: '2-digit'
                }).format(messageDate)
        }
        
        // If it's within the last week, show day name
        const daysDiff = Math.floor((now - messageDate) / (1000 * 60 * 60 * 24))
        if (daysDiff < 7) {
                return new Intl.DateTimeFormat('en-US', { 
                        weekday: 'short'
                }).format(messageDate)
        }
        
        // Otherwise show date
        return new Intl.DateTimeFormat('en-US', { 
                month: 'short', 
                day: 'numeric'
        }).format(messageDate)
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

.line-clamp-1 {
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
</style>