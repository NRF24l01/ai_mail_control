<template>
    <div class="flex flex-col w-full max-w-7xl mt-1 mx-auto bg-gray-100 overflow-hidden" style="height: calc(100vh - 58px);">
        <!-- Header -->
        <div class="flex items-center p-4 bg-white shadow z-10 relative">
            <router-link to="/dialogs" class="text-gray-600 hover:text-gray-900 transition-colors">
                <i class="fas fa-arrow-left hover:scale-110 transition-transform"></i>
            </router-link>
            <div class="flex flex-col ml-3">
                <div class="text-xl font-bold flex items-center">
                    {{ chatId || '...' }}
                </div>
            </div>
            <!-- Кнопка обновления и recognized справа -->
            <div class="absolute right-4 top-1/2 -translate-y-1/2 flex items-center space-x-2">
                <button 
                    @click="regenerate"
                    class="text-gray-700 hover:bg-gray-200 hover:text-gray-900 rounded-2xl px-3 py-1 transition-all flex items-center"
                    :disabled="isRegenerating"
                    title="Обновить recognized"
                >
                    <i class="fas fa-sync-alt animate-spin" v-if="isRegenerating"></i>
                    <i class="fas fa-sync-alt" v-else></i>
                </button>
                <span 
                    v-if="recognizedResult !== null" 
                    class="text-sm text-gray-700 px-2 py-1 hover:bg-gray-200 rounded transition-colors cursor-help"
                    :title="`Сообщение было распознано как: ${recognizedResult}`"
                >
                    {{ recognizedResult }}
                </span>
            </div>
        </div>

        <!-- Chat messages -->
        <div 
            ref="messagesContainer" 
            class="flex-1 overflow-y-auto p-4 space-y-3 pb-16"
            style="height: auto;"
        >
            <div v-if="isLoading" class="space-y-3">
                <div v-for="i in 3" :key="i" class="animate-pulse flex" :class="i % 2 === 0 ? 'justify-end' : 'justify-start'">
                    <div class="h-10 rounded-lg w-48" :class="i % 2 === 0 ? 'bg-blue-200' : 'bg-gray-200'"></div>
                </div>
            </div>
            
            <template v-else>
                <div v-for="(msg, index) in messages" :key="msg.id" 
                     class="message-item"
                     :class="[
                         'flex',
                         msg.from === 'me' ? 'justify-end' : 'justify-start',
                         isSameAuthor(index) ? 'mt-1' : 'mt-3'
                     ]">
                    <div class="flex items-end gap-2">
                        <div :class="[
                                'max-w-xs px-4 py-2 rounded-lg group relative hover:shadow-md transition-shadow',
                                msg.from === 'me' 
                                    ? 'bg-blue-500 text-white rounded-tr-none' 
                                    : 'bg-gray-200 text-gray-900 rounded-tl-none'
                            ]"
                        >
                            <div class="font-semibold text-sm mb-1" v-if="msg.subject">
                                {{ msg.subject }}
                            </div>
                            {{ msg.text }}
                            <div class="text-xs mt-1 opacity-70 flex items-center gap-1" 
                                 :class="msg.from === 'me' ? 'text-blue-100' : 'text-gray-500'">
                                {{ formatTime(msg.time) }}
                            </div>
                        </div>
                    </div>
                </div>
            </template>
        </div>

        <!-- Message input section (sticky) -->
        <div class="sticky bottom-0 left-0 right-0 bg-white border-t shadow-md">
            <form @submit.prevent="sendMessage" class="flex items-center p-4 bg-white">
                <div class="relative flex-1">
                    <input
                        v-model="newMessage"
                        type="text"
                        placeholder="Введите сообщение..."
                        class="w-full border rounded-full px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300 transition-all"
                    />
                </div>
                <button
                    type="submit"
                    class="ml-2 bg-blue-500 text-white p-2 rounded-full hover:bg-blue-600 transition-all w-10 h-10 flex items-center justify-center send-btn"
                    :class="{ 'sending': isSending }"
                >
                    <i class="fas fa-paper-plane"></i>
                </button>
            </form>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const chatId = ref(route.params.chatId)
const isLoading = ref(true)
const messages = ref([])
const user = ref({})
const newMessage = ref('')
const messagesContainer = ref(null)
const isSending = ref(false)

// Новые переменные для regenerate
const isRegenerating = ref(false)
const recognizedResult = ref(null)

async function fetchMessages(chatId) {
    const url = `${import.meta.env.VITE_BACKEND_URL}/chat/${chatId}`
    const token = localStorage.getItem('authToken');
    try {
        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'Authorization': token ? `Bearer ${token}` : '',
            'Content-Type': 'application/json'
          }
        })
        if (response.status === 401) {
            console.log("Получен 401, выполняем редирект на /")
            window.location.replace("/")
            return []
        }
        if (!response.ok) throw new Error('Ошибка загрузки сообщений')
        const data = await response.json()
        // Преобразуем данные из MailResponse к формату сообщений чата
        const chatMessages = data.chat.map((mail, idx) => ({
            id: mail.message_id || idx,
            from: mail.type === "INBOX" ? 'other' : 'me',
            subject: mail.subject || 'Без темы',
            text: mail.body,
            time: mail.date,
            read: true,
            recognized: mail.recognized,
            pre_generated_answer: mail.pre_generated_answer
        }))
        // recognized для отображения
        const recognizedMsg = chatMessages.find(msg => msg.recognized !== null)
        if (recognizedMsg) {
            recognizedResult.value = recognizedMsg.recognized
        } else {
            recognizedResult.value = null
        }
        // Если есть сообщение с recognized !== null, задаем newMessage
        if (recognizedMsg && recognizedMsg.pre_generated_answer) {
            newMessage.value = recognizedMsg.pre_generated_answer
        }
        // Возвращаем только нужные поля для сообщений
        return chatMessages.map(({id, from, subject, text, time, read}) => ({
            id, from, subject, text, time, read
        }))
    } catch (error) {
        console.error('Ошибка запроса чата:', error)
        return []
    }
}

function fetchUser() {
    return {
        email: chatId.value,
        fullName: 'Иванов Иван Иванович',
        phone: '+7 999 123-45-67'
    }
}

onMounted(async () => {
    try {
        messages.value = await fetchMessages(chatId.value)
        user.value = await fetchUser()
        isLoading.value = false
        
        await nextTick()
        scrollToBottom()
    } catch (error) {
        console.error('Error loading chat data:', error)
        isLoading.value = false
    }
})

watch(messages, () => {
    nextTick(() => {
        scrollToBottom()
    })
})

function scrollToBottom() {
    nextTick(() => {
        if (messagesContainer.value) {
            messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
        }
    })
}

function sendMessage() {
    if (!newMessage.value.trim()) return
    
    isSending.value = true
    
    const newMsg = {
        id: Date.now(),
        from: 'me',
        text: newMessage.value,
        time: new Date().toISOString(),
        read: false
    }
    
    setTimeout(() => {
        messages.value.push(newMsg)
        newMessage.value = ''
        isSending.value = false
    }, 300)
}

function formatTime(time) {
    const date = new Date(time)
    return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}

function isSameAuthor(index) {
    if (index === 0) return false
    return messages.value[index].from === messages.value[index - 1].from
}

async function regenerate() {
    if (!chatId.value) return
    isRegenerating.value = true
    try {
        const url = `${import.meta.env.VITE_BACKEND_URL}/regenerate/${chatId.value}`
        const response = await fetch(url, { method: 'POST' })
        if (!response.ok) throw new Error('Ошибка запроса regenerate')
        const data = await response.json()
        // Ожидаем, что recognized в ответе
        recognizedResult.value = data.recognized ?? null
        // Можно обновить сообщения, если нужно
        messages.value = await fetchMessages(chatId.value)
    } catch (error) {
        console.error('Ошибка regenerate:', error)
    } finally {
        isRegenerating.value = false
    }
}
</script>

<style scoped>
.group:hover .group-hover\:opacity-100 {
    opacity: 1;
    transition: opacity 0.2s;
}

.message-item {
    animation: fadeIn 0.3s ease-in-out;
    transition: transform 0.2s;
}

.message-item:hover {
    transform: translateY(-1px);
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.send-btn {
    transition: all 0.2s ease;
}

.send-btn.sending {
    transform: scale(0.8) rotate(20deg);
}
</style>