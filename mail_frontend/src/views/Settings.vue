<template>
    <div class="max-w-2xl mx-auto p-6">
        <h1 class="text-2xl font-bold mb-6">Settings</h1>
        
        <div v-if="isLoading" class="flex justify-center my-8">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
        
        <form v-else @submit.prevent="saveSettings" class="space-y-6">
            <div class="space-y-2">
                <label for="gpt-prompt" class="block font-semibold">GPT Prompt</label>
                <textarea 
                    id="gpt-prompt"
                    v-model="formData.gpt_prompt" 
                    class="w-full border border-gray-200 rounded p-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    rows="3"
                ></textarea>
            </div>
            
            <div class="space-y-2">
                <label for="gpt-model" class="block font-semibold">GPT Model</label>
                <input 
                    id="gpt-model"
                    v-model="formData.gpt_model" 
                    class="w-full border border-gray-200 rounded p-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500" 
                />
            </div>
            
            <div class="space-y-4 mt-8">
                <div class="flex justify-between items-center">
                    <h2 class="font-semibold text-lg">Types & Standard Answers</h2>
                    <span class="text-sm text-gray-500">{{ formData.types.length }} items</span>
                </div>
                
                <div v-if="formData.types.length === 0" 
                     class="bg-gray-50 rounded-lg p-8 text-center border border-dashed border-gray-300">
                    <div class="text-gray-500 mb-2">No types added yet</div>
                    <div class="text-sm text-gray-400">Add your first type and standard answer below</div>
                </div>
                
                <div v-else class="space-y-3">
                    <transition-group name="fade-card" tag="div">
                        <div
                            v-for="(type, idx) in formData.types"
                            :key="`type-${idx}`"
                            class="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden transition-all hover:shadow-md mb-4"
                        >
                            <div class="flex items-start p-4">
                                <div class="flex-1 space-y-3">
                                    <div>
                                        <label :for="`type-${idx}`" class="block text-xs font-medium text-gray-500 mb-1">Type</label>
                                        <input 
                                            :id="`type-${idx}`"
                                            v-model="formData.types[idx]" 
                                            :placeholder="'Enter type name'"
                                            class="w-full border border-gray-200 rounded p-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500" 
                                            ref="typeInputRefs"
                                            :ref="el => typeInputRefs[idx] = el"
                                            @input="handleTypeCardInput(idx)"
                                        />
                                    </div>
                                    <div>
                                        <label :for="`answer-${idx}`" class="block text-xs font-medium text-gray-500 mb-1">Standard Answer</label>
                                        <input 
                                            :id="`answer-${idx}`"
                                            v-model="formData.answers[type]" 
                                            :placeholder="'Enter standard response'"
                                            class="w-full border border-gray-200 rounded p-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500" 
                                            ref="answerInputRefs"
                                            :ref="el => answerInputRefs[idx] = el"
                                            @input="handleTypeCardInput(idx)"
                                        />
                                    </div>
                                </div>
                                <button 
                                    type="button" 
                                    @click="confirmRemoveType(idx)" 
                                    class="ml-3 bg-white text-red-500 hover:text-red-700 p-1 rounded-full hover:bg-red-50 transition-colors"
                                    aria-label="Remove type"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                        <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
                                    </svg>
                                </button>
                            </div>
                        </div>
                    </transition-group>
                </div>
                
                <div class="mt-6 bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <h3 class="text-sm font-medium text-gray-700 mb-3">Add New Type</h3>
                    <div class="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-3">
                        <div class="flex-1">
                            <label for="new-type" class="block text-xs text-gray-500 mb-1">Type</label>
                            <input 
                                id="new-type"
                                v-model="newType" 
                                placeholder="Enter type name" 
                                class="w-full border border-gray-200 rounded p-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500" 
                                @input="handleNewTypeInput"
                            />
                        </div>
                        <div class="flex-1">
                            <label for="new-answer" class="block text-xs text-gray-500 mb-1">Standard Answer</label>
                            <input 
                                id="new-answer"
                                v-model="newTypeAnswer" 
                                placeholder="Enter standard response" 
                                class="w-full border border-gray-200 rounded p-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500" 
                                @input="handleNewAnswerInput"
                            />
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="space-y-2">
                <label for="tg-admins" class="block font-semibold">Telegram Admins</label>
                <div class="flex flex-col space-y-2">
                    <div v-for="(user, idx) in formData.tg_users" :key="`tg-user-${idx}`" class="flex items-center space-x-2">
                        <input
                            type="number"
                            :id="`tg-user-${idx}`"
                            v-model.number="formData.tg_users[idx]"
                            class="w-full border border-gray-200 rounded p-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="Telegram User ID"
                        />
                        <button
                            type="button"
                            @click="removeTgUser(idx)"
                            class="bg-white text-red-500 hover:text-red-700 p-1 rounded-full hover:bg-red-50 transition-colors"
                            aria-label="Remove Telegram Admin"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M6 6a1 1 0 011.414 0L10 8.586l2.586-2.586A1 1 0 1114 7.414L11.414 10l2.586 2.586a1 1 0 01-1.414 1.414L10 11.414l-2.586 2.586A1 1 0 115.414 13.414L8 10.828l-2.586-2.586A1 1 0 116 6z" clip-rule="evenodd"/>
                            </svg>
                        </button>
                    </div>
                    <div class="flex items-center space-x-2">
                        <input
                            type="number"
                            v-model.number="newTgUser"
                            class="w-full border border-gray-200 rounded p-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="Add Telegram User ID"
                            @keyup.enter="addTgUser"
                        />
                        <button
                            type="button"
                            @click="addTgUser"
                            class="bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700"
                        >Add</button>
                    </div>
                </div>
            </div>
            
            <div class="flex items-center space-x-4 pt-4">
                <button 
                    type="submit" 
                    class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 flex items-center"
                    :disabled="isSaving"
                >
                    <span v-if="isSaving" class="mr-2 h-4 w-4 border-t-2 border-white rounded-full animate-spin"></span>
                    {{ isSaving ? 'Saving...' : 'Save Settings' }}
                </button>
                <span v-if="message" :class="{'text-green-600': isSuccess, 'text-red-600': !isSuccess}">
                    {{ message }}
                </span>
            </div>
        </form>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, nextTick } from 'vue'

const formData = reactive({
    gpt_prompt: '',
    gpt_model: '',
    answers: {},
    types: [],
    tg_users: []
})

const newType = ref('')
const newTypeAnswer = ref('')
const newTgUser = ref('')
const message = ref('')
const isSuccess = ref(true)
const isLoading = ref(true)
const isSaving = ref(false)
const typeInputRefs = ref([])
const answerInputRefs = ref([])
let lastAddedIdx = ref(null)
let lastFocusField = ref('type') // 'type' or 'answer'

const VITE_BACKEND_URL = import.meta.env.VITE_BACKEND_URL

// Keep answers in sync with type name changes
watch(() => [...formData.types], (newTypes, oldTypes) => {
    if (!oldTypes || oldTypes.length === 0) return
    
    // Handle type name changes
    oldTypes.forEach((oldType, index) => {
        if (index < newTypes.length && oldType !== newTypes[index]) {
            const answer = formData.answers[oldType]
            if (answer) {
                formData.answers[newTypes[index]] = answer
                delete formData.answers[oldType]
            }
        }
    })
})

onMounted(async () => {
    try {
        const token = localStorage.getItem('authToken');
        const res = await fetch(`${VITE_BACKEND_URL}/settings`, {
          method: 'GET',
          headers: {
            'Authorization': token ? `Bearer ${token}` : '',
            'Content-Type': 'application/json'
          }
        })
        if (res.status === 401) {
            console.log("Получен 401, выполняем редирект на /")
            window.location.replace("/")
            return []
        }
        if (res.ok) {
            const data = await res.json()
            Object.assign(formData, {
                gpt_prompt: data.gpt_prompt || '',
                gpt_model: data.gpt_model || '',
                answers: data.answers || {},
                types: data.types || [],
                tg_users: Array.isArray(data.tg_users) ? data.tg_users : []
            })
        } else {
            showMessage('Error loading settings', false)
        }
    } catch (error) {
        showMessage(`Failed to load settings: ${error.message}`, false)
    } finally {
        isLoading.value = false
    }
})

function setTypeInputRef(idx, el) {
    if (el) {
        typeInputRefs.value[idx] = el
        // Focus only if this is the last added index
        if (lastAddedIdx.value === idx) {
            el.focus()
            lastAddedIdx.value = null
        }
    }
}

function addTypeWithAnswer() {
    if (newType.value) {
        if (!formData.types.includes(newType.value)) {
            formData.types.push(newType.value)
            formData.answers[newType.value] = newTypeAnswer.value
        } else {
            showMessage(`Type "${newType.value}" already exists`, false)
        }
        newType.value = ''
        newTypeAnswer.value = ''
    }
}

function clearNewType() {
    // Always keep fields as they are, but this can be used to reset if needed
    // For now, do nothing
}

function tryAddType() {
    // Only add if both fields are filled, type is not duplicate, and not empty
    if (newType.value && newTypeAnswer.value && !formData.types.includes(newType.value)) {
        formData.types.push(newType.value)
        formData.answers[newType.value] = newTypeAnswer.value
        newType.value = ''
        newTypeAnswer.value = ''
    } else if (!newType.value && !newTypeAnswer.value) {
        // If both fields are empty, do nothing
    } else if (formData.types.includes(newType.value)) {
        showMessage(`Type "${newType.value}" already exists`, false)
        newType.value = ''
        newTypeAnswer.value = ''
    }
}

function confirmRemoveType(idx) {
    if (confirm(`Are you sure you want to remove "${formData.types[idx]}"?`)) {
        removeType(idx)
    }
}

function removeType(idx) {
    const type = formData.types[idx]
    formData.types.splice(idx, 1)
    delete formData.answers[type]
}

function showMessage(msg, success = true) {
    message.value = msg
    isSuccess.value = success
    setTimeout(() => {
        message.value = ''
    }, 5000)
}

async function saveSettings() {
    try {
        isSaving.value = true
        const payload = {
            gpt_prompt: formData.gpt_prompt,
            gpt_model: formData.gpt_model,
            answers: formData.answers,
            types: formData.types,
            tg_users: formData.tg_users
        }
        const res = await fetch(`${VITE_BACKEND_URL}/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        
        if (res.ok) {
            showMessage('Settings saved successfully!', true)
        } else {
            const errorData = await res.json().catch(() => ({}))
            showMessage(`Error saving settings: ${errorData.message || res.statusText}`, false)
        }
    } catch (error) {
        showMessage(`Failed to save: ${error.message}`, false)
    } finally {
        isSaving.value = false
    }
}

function addTgUser() {
    const val = Number(newTgUser.value)
    if (!val || isNaN(val)) {
        showMessage('Please enter a valid Telegram User ID', false)
        return
    }
    if (formData.tg_users.includes(val)) {
        showMessage('This Telegram User ID is already added', false)
        newTgUser.value = ''
        return
    }
    formData.tg_users.push(val)
    newTgUser.value = ''
}

function removeTgUser(idx) {
    formData.tg_users.splice(idx, 1)
}

function handleNewTypeInput(e) {
    // Create new card if user starts typing in type or answer
    if (!e.target.value && !newTypeAnswer.value) return
    if (formData.types.includes(e.target.value)) {
        showMessage(`Type "${e.target.value}" already exists`, false)
        newType.value = ''
        return
    }
    if (e.target.value) {
        formData.types.push(e.target.value)
        formData.answers[e.target.value] = newTypeAnswer.value || ''
        const idx = formData.types.length - 1
        newType.value = ''
        newTypeAnswer.value = ''
        lastFocusField.value = 'type'
        nextTick(() => {
            if (typeInputRefs.value[idx]) {
                typeInputRefs.value[idx].focus()
            }
        })
    }
}

function handleNewAnswerInput(e) {
    // Create new card if user starts typing in type or answer
    if (!e.target.value && !newType.value) return
    if (newType.value && formData.types.includes(newType.value)) {
        showMessage(`Type "${newType.value}" already exists`, false)
        newType.value = ''
        newTypeAnswer.value = ''
        return
    }
    if (newType.value || e.target.value) {
        const typeToAdd = newType.value
        formData.types.push(typeToAdd)
        formData.answers[typeToAdd] = e.target.value
        const idx = formData.types.length - 1
        newType.value = ''
        newTypeAnswer.value = ''
        lastFocusField.value = 'answer'
        nextTick(() => {
            if (answerInputRefs.value[idx]) {
                answerInputRefs.value[idx].focus()
            }
        })
    }
}

function handleTypeCardInput(idx) {
    // Remove card if both fields are empty (type and answer)
    const typeVal = formData.types[idx]
    // Correctly get answer value by index, not by type key
    let answerVal = ''
    // Find the answer by index in types array
    if (formData.types[idx] in formData.answers) {
        answerVal = formData.answers[formData.types[idx]]
    } else {
        // If type is empty, try to find answer by previous type value (not reliable, but fallback)
        answerVal = ''
    }
    // Remove if both are empty (do not remove if answer has value, even if type is empty)
    if ((!typeVal || typeVal.trim() === '') && (!answerVal || answerVal.trim() === '')) {
        formData.types.splice(idx, 1)
        Object.keys(formData.answers).forEach(key => {
            if (!key || key.trim() === '') delete formData.answers[key]
        })
        typeInputRefs.value.splice(idx, 1)
        answerInputRefs.value.splice(idx, 1)
    }
}
</script>

<style scoped>
.fade-card-enter-active, .fade-card-leave-active {
    transition: opacity 0.3s;
}
.fade-card-enter-from, .fade-card-leave-to {
    opacity: 0;
}
.fade-card-leave-from, .fade-card-enter-to {
    opacity: 1;
}
.mb-4 {
    margin-bottom: 1rem;
}
</style>