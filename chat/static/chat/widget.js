/* Floating chat bubble for your store. Add before </body>:
   <script src="https://YOUR-CHATBOT-DOMAIN/static/chat/widget.js" data-src="https://YOUR-CHATBOT-DOMAIN/"></script>
*/
(function () {
  var s = document.currentScript;
  var src = s && s.getAttribute("data-src");
  if (!src) return;

  var btn = document.createElement("button");
  btn.setAttribute("aria-label", "Chat with BeyondConnect");
  btn.textContent = "💬";
  btn.style.cssText = "position:fixed;right:20px;bottom:20px;width:58px;height:58px;border-radius:50%;border:0;" +
    "background:#ea580c;color:#fff;font-size:26px;cursor:pointer;box-shadow:0 6px 20px rgba(0,0,0,.25);z-index:2147483646";

  var frame = document.createElement("iframe");
  frame.src = src;
  frame.title = "BeyondConnect Assistant";
  frame.style.cssText = "position:fixed;right:20px;bottom:90px;width:380px;max-width:calc(100vw - 24px);" +
    "height:600px;max-height:calc(100vh - 110px);border:0;border-radius:16px;box-shadow:0 10px 40px rgba(0,0,0,.3);" +
    "display:none;z-index:2147483646;background:#fff";

  btn.onclick = function () {
    var open = frame.style.display === "none";
    frame.style.display = open ? "block" : "none";
    btn.textContent = open ? "✕" : "💬";
  };
  document.body.appendChild(frame);
  document.body.appendChild(btn);
})();
