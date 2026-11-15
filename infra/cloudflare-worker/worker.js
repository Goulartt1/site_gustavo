// Worker do Cloudflare: porta de entrada do site.
//
// Recebe as visitas de gustavolocks.com.br e repassa ao Cloud Run, enviando:
// - X-Forwarded-Host: o domínio original (o Django usa para montar links);
// - X-Origin-Secret: a "senha" que prova ao Django que a visita veio daqui;
// - X-Client-IP: o IP do visitante (usado no limite de envios dos formulários).
// Arquivos estáticos (CSS, fontes) ficam em cache no Cloudflare por 1 ano:
// têm o hash do conteúdo no nome, então nunca ficam desatualizados.
//
// Variáveis configuradas no painel do Cloudflare (Settings > Variables):
// - CLOUD_RUN_URL  (texto): endereço .run.app do serviço
// - ORIGIN_SECRET  (secret): o mesmo valor do segredo ORIGIN_SECRET no Google

export default {
  async fetch(request, env) {
    const incoming = new URL(request.url);
    const target = new URL(incoming.pathname + incoming.search, env.CLOUD_RUN_URL);

    const proxied = new Request(target, request);
    proxied.headers.set("X-Forwarded-Host", incoming.host);
    proxied.headers.set("X-Forwarded-Proto", "https");
    proxied.headers.set("X-Origin-Secret", env.ORIGIN_SECRET);
    // CF-Connecting-IP é preenchido pelo Cloudflare com o IP de quem visitou.
    proxied.headers.set("X-Client-IP", request.headers.get("CF-Connecting-IP") || "");

    if (incoming.pathname.startsWith("/static/")) {
      return fetch(proxied, { cf: { cacheEverything: true, cacheTtl: 31536000 } });
    }
    return fetch(proxied);
  },
};
