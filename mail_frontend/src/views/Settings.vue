<template>
  <div class="max-w-2xl mx-auto p-6">
    <h1 class="text-2xl font-bold mb-6">Settings</h1>
    <form @submit.prevent="saveSettings" class="space-y-4">
      <div>
        <label class="block font-semibold mb-1">GPT Prompt</label>
        <textarea v-model="settings.gpt_prompt" class="w-full border rounded p-2"></textarea>
      </div>
      <div>
        <label class="block font-semibold mb-1">GPT Model</label>
        <input v-model="settings.gpt_model" class="w-full border rounded p-2" />
      </div>
      <div>
        <label class="block font-semibold mb-1">Answers (key-value)</label>
        <div v-for="(value, key) in answersObj" :key="key" class="flex space-x-2 mb-2">
          <input v-model="answersObj[key]" class="flex-1 border rounded p-2" />
          <button type="button" @click="removeAnswer(key)" class="text-red-500">Remove</button>
        </div>
        <div class="flex space-x-2">
          <input v-model="newAnswerKey" placeholder="Key" class="border rounded p-2" />
          <input v-model="newAnswerValue" placeholder="Value" class="border rounded p-2" />
          <button type="button" @click="addAnswer" class="text-green-500">Add</button>
        </div>
      </div>
      <div>
        <label class="block font-semibold mb-1">Types (array)</label>
        <div v-for="(type, idx) in typesArr" :key="idx" class="flex space-x-2 mb-2">
          <input v-model="typesArr[idx]" class="flex-1 border rounded p-2" />
          <button type="button" @click="removeType(idx)" class="text-red-500">Remove</button>
        </div>
        <div class="flex space-x-2">
          <input v-model="newType" placeholder="New type" class="border rounded p-2" />
          <button type="button" @click="addType" class="text-green-500">Add</button>
        </div>
      </div>
      <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded">Save</button>
      <div v-if="message" class="mt-4 text-green-600">{{ message }}</div>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'

const settings = reactive({
  gpt_prompt: '',
  gpt_model: '',
  answers: {},
  types: []
})

const answersObj = reactive({})
const typesArr = ref([])
const newAnswerKey = ref('')
const newAnswerValue = ref('')
const newType = ref('')
const message = ref('')

const VITE_BACKEND_URL = import.meta.env.VITE_BACKEND_URL

function syncSettingsToFields() {
  Object.assign(answersObj, settings.answers || {})
  typesArr.value = Array.isArray(settings.types) ? [...settings.types] : []
}

onMounted(async () => {
  const res = await fetch(`${VITE_BACKEND_URL}/settings`)
  if (res.ok) {
    const data = await res.json()
    settings.gpt_prompt = data.gpt_prompt
    settings.gpt_model = data.gpt_model
    settings.answers = data.answers || {}
    settings.types = data.types || []
    syncSettingsToFields()
  }
})

function addAnswer() {
  if (newAnswerKey.value) {
    answersObj[newAnswerKey.value] = newAnswerValue.value
    newAnswerKey.value = ''
    newAnswerValue.value = ''
  }
}

function removeAnswer(key) {
  delete answersObj[key]
}

function addType() {
  if (newType.value) {
    typesArr.value.push(newType.value)
    newType.value = ''
  }
}

function removeType(idx) {
  typesArr.value.splice(idx, 1)
}

async function saveSettings() {
  settings.answers = { ...answersObj }
  settings.types = [...typesArr.value]
  const res = await fetch(`${VITE_BACKEND_URL}/settings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings)
  })
  if (res.ok) {
    message.value = 'Settings saved!'
  } else {
    message.value = 'Error saving settings.'
  }
}
</script>
