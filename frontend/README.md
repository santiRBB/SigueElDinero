# Vue 3 + TypeScript + Vite

This template should help get you started developing with Vue 3 and TypeScript in Vite. The template uses Vue 3 `<script setup>` SFCs, check out the [script setup docs](https://v3.vuejs.org/api/sfc-script-setup.html#sfc-script-setup) to learn more.

Learn more about the recommended Project Setup and IDE Support in the [Vue Docs TypeScript Guide](https://vuejs.org/guide/typescript/overview.html#project-setup).

## Variables de entorno

Ver `.env.example`. Estas variables deben definirse en el entorno de despliegue (Netlify) además de en local:

- `VITE_API_URL`: URL base de la API backend. Requerida para que el frontend pueda hacer peticiones.
- `VITE_ADSENSE_PUBLISHER_ID`: ID de publisher de Google AdSense (`ca-pub-...`). Si no está definida en producción, el banner de cookies seguirá pidiendo consentimiento de publicidad pero el anuncio nunca se cargará (fallo silencioso).
- `VITE_ADSENSE_SLOT_ID`: ID del slot de anuncio de AdSense. Igual que la anterior, debe estar definida en producción para que el anuncio se muestre.
