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
                    <div v-for="(type, idx) in formData.types" :key="idx" 
                         class="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden transition-all hover:shadow-md">
                        <div class="flex items-start p-4">
                            <div class="flex-1 space-y-3">
                                <div>
                                    <label :for="`type-${idx}`" class="block text-xs font-medium text-gray-500 mb-1">Type</label>
                                    <input 
                                        :id="`type-${idx}`"
                                        v-model="formData.types[idx]" 
                                        class="w-full border border-gray-200 rounded p-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500" 
                                    />
                                </div>
                                <div>
                                    <label :for="`answer-${idx}`" class="block text-xs font-medium text-gray-500 mb-1">Standard Answer</label>
                                    <input 
                                        :id="`answer-${idx}`"
                                        v-model="formData.answers[type]" 
                                        placeholder="Enter standard response" 
                                        class="w-full border border-gray-200 rounded p-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500" 
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
                            />
                        </div>
                        <div class="flex-1">
                            <label for="new-answer" class="block text-xs text-gray-500 mb-1">Standard Answer</label>
                            <input 
                                id="new-answer"
                                v-model="newTypeAnswer" 
                                placeholder="Enter standard response" 
                                class="w-full border border-gray-200 rounded p-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500" 
                            />
                        </div>
                        <div class="flex items-end">
                            <button 
                                type="button" 
                                @click="addTypeWithAnswer" 
                                class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors h-10"
                                :disabled="!newType"
                            >
                                Add
                            </button>
                        </div>
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
import { ref, reactive, onMounted, watch } from 'vue'

const formData = reactive({
    gpt_prompt: '',
    gpt_model: '',
    answers: {},
    types: []
})

const newType = ref('')
const newTypeAnswer = ref('')
const message = ref('')
const isSuccess = ref(true)
const isLoading = ref(true)
const isSaving = ref(false)

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
        const res = await fetch(`${VITE_BACKEND_URL}/settings`)
        if (res.ok) {
            const data = await res.json()
            Object.assign(formData, {
                gpt_prompt: data.gpt_prompt || '',
                gpt_model: data.gpt_model || '',
                answers: data.answers || {},
                types: data.types || []
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
        const res = await fetch(`${VITE_BACKEND_URL}/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
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
</script>
