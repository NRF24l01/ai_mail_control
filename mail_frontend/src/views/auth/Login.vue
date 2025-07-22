<template>
    <div class="flex items-center justify-center w-full bg-white" style="height: calc(100vh - 48px);">
        <div class="w-full max-w-md p-8 rounded-lg shadow-lg bg-white border-gray-200 border">
            <h2 class="text-2xl font-bold mb-6 text-center text-gray-800">Войти</h2>
            <form @submit.prevent="handleLogin">
                <div class="mb-5">
                    <label for="email" class="block mb-2 font-medium text-gray-700">Почта</label>
                    <input
                        id="email"
                        v-model="email"
                        type="email"
                        placeholder="Введите вашу почту"
                        :class="['w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-200', errors.email ? 'border-red-400' : 'border-gray-300', 'bg-white text-gray-900']"
                    />
                    <div v-if="errors.email" class="text-red-500 text-sm mt-1">{{ errors.email }}</div>
                </div>
                <div class="mb-5">
                    <label for="password" class="block mb-2 font-medium text-gray-700">Пароль</label>
                    <input
                        id="password"
                        v-model="password"
                        type="password"
                        placeholder="Введите ваш пароль"
                        :class="['w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-200', errors.password ? 'border-red-400' : 'border-gray-300', 'bg-white text-gray-900']"
                    />
                    <div v-if="errors.password" class="text-red-500 text-sm mt-1">{{ errors.password }}</div>
                </div>
                <div v-if="loginError" class="text-red-500 text-sm mb-4 text-center">{{ loginError }}</div>
                <button
                    type="submit"
                    :disabled="loading"
                    class="w-full py-2 bg-blue-500 text-white rounded-md font-semibold hover:bg-blue-600 transition disabled:bg-gray-300 disabled:text-gray-500"
                >
                    {{ loading ? 'Входим...' : 'Войти' }}
                </button>
            </form>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue';

const email = ref('');
const password = ref('');
const errors = ref({});
const loginError = ref('');
const loading = ref(false);

function validate() {
    const newErrors = {};
    // Email validation
    if (!email.value) {
        newErrors.email = "Почта необходима.";
    } else if (
        !/^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(email.value)
    ) {
        newErrors.email = "Почта должна быть валидной.";
    }
    // Password validation
    if (!password.value) {
        newErrors.password = "Пароль необходим.";
    } else if (password.value.length < 6) {
        newErrors.password = "Как минимум 6 символов пароля.";
    }
    errors.value = newErrors;
    return Object.keys(newErrors).length === 0;
}

async function handleLogin() {
    loginError.value = "";
    if (!validate()) return;
    loading.value = true;
    await new Promise((resolve) => setTimeout(resolve, 1000));
    const result = Math.floor(Math.random() * 3);
    if (result === 0) {
        alert("Вы вошли!");
        email.value = "";
        password.value = "";
    } else if (result === 1) {
        loginError.value = "Не правильные данные для входа.";
    } else {
        loginError.value = "Сервер не отвечает, попробуйте позже.";
    }
    loading.value = false;
}
</script>

<style scoped>
.login-container {
    max-width: 400px;
    margin: 40px auto;
    padding: 32px;
    border: 1px solid #eee;
    border-radius: 8px;
    background: #fafafa;
}
.form-group {
    margin-bottom: 20px;
}
label {
    display: block;
    margin-bottom: 6px;
    font-weight: 500;
}
input {
    width: 100%;
    padding: 8px;
    border: 1px solid #bbb;
    border-radius: 4px;
    font-size: 16px;
}
.input-error {
    border-color: #e74c3c;
}
.error-message {
    color: #e74c3c;
    font-size: 14px;
    margin-top: 4px;
}
button {
    width: 100%;
    padding: 10px;
    background: #3498db;
    color: #fff;
    border: none;
    border-radius: 4px;
    font-size: 16px;
    cursor: pointer;
}
button:disabled {
    background: #95a5a6;
    cursor: not-allowed;
}
</style>
