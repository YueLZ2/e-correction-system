// src/index.js
import { createApp } from 'vue';
import App from './App.vue';
import store from './store/bpmn';
import './assets/main.css';

const app = createApp(App);
app.use(store);
app.mount('#app');

// Global error handler
app.config.errorHandler = (err, vm, info) => {
  console.error('Global error:', err);
  console.error('Error info:', info);
};