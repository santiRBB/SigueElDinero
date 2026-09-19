<script setup lang="ts">
import { openCookiePreferences } from '../utils/cookieConsent'
</script>

<template>
  <section class="page-head">
    <p class="kicker">Legal</p>
    <h1 class="h-page">Política de cookies</h1>
  </section>
  <section class="prose">
    <p>
      Esta web usa el mínimo de cookies y almacenamiento local necesario para funcionar y, si las
      aceptas, para mostrar publicidad y un widget de apoyo al proyecto. Nada de lo descrito abajo se
      activa hasta que lo aceptas explícitamente, salvo la cookie que recuerda tu propia elección.
    </p>
    <h2>Necesarias</h2>
    <p>
      Una cookie propia llamada <code>cc_cookie</code> guarda qué categorías has aceptado o rechazado,
      para no volver a preguntarte en cada visita. No requiere tu consentimiento porque es
      imprescindible para que el propio sistema de cookies funcione.
    </p>
    <h2>Publicidad</h2>
    <p>
      Si aceptas esta categoría se carga <strong>Google AdSense</strong>, que puede instalar sus
      propias cookies para mostrar y medir el anuncio. Google no publica una lista fija de esas
      cookies porque puede cambiarlas; puedes consultar cuáles usa y cómo gestionarlas en su
      <a href="https://policies.google.com/technologies/cookies" target="_blank" rel="noopener"
        >política de cookies</a
      >.
    </p>
    <h2>Apoyo al proyecto</h2>
    <p>
      Si aceptas esta categoría se carga el widget de <strong>Buy Me a Coffee</strong>, que permite
      invitarme a un café para apoyar el mantenimiento del proyecto. Puede instalar sus propias
      cookies para su funcionamiento; su
      <a href="https://buymeacoffee.com/privacy-policy" target="_blank" rel="noopener"
        >política de privacidad</a
      >
      detalla cuáles.
    </p>
    <h2>Cambiar tu elección</h2>
    <p>
      Puedes aceptar, rechazar o cambiar cada categoría cuando quieras.
      <button type="button" class="link-btn" @click="openCookiePreferences">
        Abrir preferencias de cookies
      </button>
    </p>
  </section>
</template>

<style scoped>
.prose {
  max-width: 66ch;
}
.link-btn {
  all: unset;
  cursor: pointer;
  font-family: inherit;
  font-size: inherit;
  color: var(--navy);
  border-bottom: 1px solid rgba(11, 59, 92, 0.3);
}
.link-btn:hover {
  color: var(--amber);
  border-bottom-color: var(--amber);
}
</style>
