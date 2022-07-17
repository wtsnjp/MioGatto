(()=>{"use strict";function t(t){return t.replace(/[ !"#$%&'()*+,.\/:;<=>?@\[\\\]^`{|}~]/g,"\\$&")}function e(t){let e={};var o;e.hex=(o=t.text(),Array.from((new TextEncoder).encode(o)).map((t=>t.toString(16))).join("")),e.var="default";let n=t.attr("mathvariant");null!=n&&(e.var="normal"==n?"roman":n);let i=t.data("math-concept");return null!=i&&(e.concept=Number(i)),e}$((function(){let t=$("#option-limited-highlight");"true"==localStorage["option-limited-highlight"]?(t.prop("checked",!0),u(!0)):u(!1),t.on("click",(function(){$(this).prop("checked")?(localStorage["option-limited-highlight"]="true",u(!0)):(localStorage["option-limited-highlight"]="false",u(!1))}))})),$((function(){$(".sidebar-tab input.tab-title").each((function(){let t=this.id;"true"==localStorage[t]&&$(`#${t}`).prop("checked",!0),$(`#${t}`).on("change",(function(){$(this).prop("checked")?localStorage[t]=!0:localStorage[t]=!1}))}))}));let o={};$.ajax({url:"/mcdict.json",dataType:"json",async:!1,success:function(t){o=t}});let n=["#008b8b","#ff7f50","#ff4500","#2f4f4f","#006400","#dc143c","#c71585","#4169e1","#2e8b57","#ff1493","#191970","#ff69b4","#ff69b4","#0000cd","#f4a460","#ff00ff","#7cfc00","#d2691e","#a0522d","#800000","#9400d3","#556b2f","#4b0082","#808000"],i=0;for(let t in o)for(let e in o[t])for(let l in o[t][e])null!=o[t][e][l].description&&(o[t][e][l].color=n[i%n.length],i++);function l(t){return null!=t.concept?o[t.hex][t.var][t.concept]:void 0}function c(t){if(null!=o[t.hex])return o[t.hex][t.var]}function a(t){let o=l(e(t));null!=o&&null!=o.color&&t.attr("mathcolor",o.color)}$((function(){$("mi").each((function(){a($(this))}))}));let s={};function r(t,e,o){let n=l(e);var i;null==n||null==n.color?(t.css("text-decoration","underline"),t.css("text-decoration-color","#FF0000"),t.css("text-decoration-thickness","2px")):t.css("background-color",`rgba(${(i=n.color,"#"==i.slice(0,1)&&(i=i.slice(1)),3==i.length&&(i=i.slice(0,1)+i.slice(0,1)+i.slice(1,2)+i.slice(1,2)+i.slice(2,3)+i.slice(2,3)),[i.slice(0,2),i.slice(2,4),i.slice(4,6)].map((function(t){return parseInt(t,16)}))).join()},0.3)`),t.attr({"data-sog-mi":o.mi_id,"data-sog-start":o.start_id,"data-sog-stop":o.stop_id})}function d(t){t.css("text-decoration",""),t.css("text-decoration-color",""),t.css("text-decoration-thickness",""),t.css("background-color","")}function u(o){for(let n of s.sog){let i;if(n.start_id==n.stop_id)i=$("#"+t(n.start_id));else{let e=$("#"+t(n.start_id)),o=$("#"+t(n.stop_id));i=e.nextUntil("#"+t(n.stop_id)).addBack().add(o)}let l=e($("#"+t(n.mi_id)));if(o&&null!=sessionStorage.mi_id){let o=e($("#"+t(sessionStorage.mi_id)));o.hex==l.hex&&o.var==l.var||d(i)}}for(let n of s.sog){let i;if(n.start_id==n.stop_id)i=$("#"+t(n.start_id));else{let e=$("#"+t(n.start_id)),o=$("#"+t(n.stop_id));i=e.nextUntil("#"+t(n.stop_id)).addBack().add(o)}let l=e($("#"+t(n.mi_id)));if(o&&null!=sessionStorage.mi_id){let o=e($("#"+t(sessionStorage.mi_id)));o.hex==l.hex&&o.var==l.var&&r(i,l,n)}else r(i,l,n)}}$.ajax({url:"/sog.json",dataType:"json",async:!1,success:function(t){s=t}}),$((function(){$(document).tooltip({show:!1,hide:!1,items:"[data-math-concept]",content:function(){let t=l(e($(this)));if(null!=t){let e="NONE";return t.args_type.length>0&&(e=t.args_type.join(", ")),`${t.description} <span style="color: #808080;">[${e}] (arity: ${t.arity})</span>`}return"(No description)"},open:function(t,e){$("mi").each((function(){a($(this))}))}})})),$((function(){function n(n){n.attr("style","border: dotted 2px #000000; padding: 10px;");let l=e(n),s=c(l),r=n.attr("id");if(null!=s&&null!=r)if(s.length>0)!function(n,l,c){let s=`<input type="hidden" name="mi_id" value="${n}" />`,r="";for(let t in c){let e=c[t],o=`<input type="radio" name="concept" id="c${t}" value="${t}" ${Number(t)==l.concept?"checked":""} />`,i="NONE";e.args_type.length>0&&(i=e.args_type.join(", ")),r+=`${o}<span class="keep"><label for="c${t}">\n${e.description} <span style="color: #808080;">[${i}] (arity: ${e.arity})</span>\n(<a class="edit-concept" data-mi="${n}" data-concept="${t}" href="javascript:void(0);">edit</a>)\n</label></span>`}let d=`<p>ID: <span style="font-family: monospace;">${n}</span><hr color="#FFF"><form id="form-${n}" method="POST">${s+`<div class="keep">${r}</div><p><button id="assign-concept">Assign</button> <button id="remove-concept" type="button">Remove</button> <button id="new-concept" type="button">New</button></p>`}</form></p>`,u=$("#anno-box");u.html(d),$("button#assign-concept").button(),$("button#assign-concept").on("click",(function(){let e=u.find(`#form-${t(n)}`);if(!($(`#form-${t(n)} input:checked`).length>0))return alert("Please select a concept."),!1;localStorage.scroll_top=$(window).scrollTop(),e.attr("action","/_concept"),e.trigger("submit")})),$("button#remove-concept").button(),$("button#remove-concept").on("click",(function(){let e=u.find(`#form-${t(n)}`);e.attr("action","/_remove_concept"),e.trigger("submit")})),i(l),$("a.edit-concept").on("click",(function(){let n=$(this).attr("data-mi"),i=$(this).attr("data-concept");null!=n&&null!=i&&function(t,e){let n=$("#concept-dialog-template").clone();n.removeAttr("id");let i=n.find("#concept-form");i.attr("action","/_update_concept");let l=o[t.hex][t.var][e];i.find("textarea").text(l.description),i.find('input[name="arity"]').attr("value",l.arity),l.args_type.forEach((function(t,e){i.find(`select[name="args_type${e}"]`).find(`option[value="${t}"]`).prop("selected",!0)})),n.dialog({modal:!0,title:"Edit Concept",width:500,buttons:{OK:function(){localStorage.scroll_top=$(window).scrollTop(),i.append(`<input type="hidden" name="idf_hex" value="${t.hex}" />`),i.append(`<input type="hidden" name="idf_var" value="${t.var}" />`),i.append(`<input type="hidden" name="concept_id" value="${e}" />`),i.trigger("submit")},Cancel:function(){$(this).dialog("close")}}})}(e($("#"+t(n))),Number(i))})),$("mi").each((function(){a($(this))}))}(r,l,s);else{let t=`<p>ID: <span style="font-family: monospace;">${r}</span><hr color="#FFF"><p>No concept is available.</p><p><button id="new-concept" type="button">New</button></p></p>`;$("#anno-box").html(t),i(l)}}function i(t){$("button#new-concept").button(),$("button#new-concept").on("click",(function(){let e=$("#concept-dialog-template").clone();e.attr("id","concept-dialog"),e.removeClass("concept-dialog");let o=e.find("#concept-form");o.attr("action","/_new_concept"),e.dialog({modal:!0,title:"New Concept",width:500,buttons:{OK:function(){localStorage.scroll_top=$(window).scrollTop(),o.append(`<input type="hidden" name="idf_hex" value="${t.hex}" />`),o.append(`<input type="hidden" name="idf_var" value="${t.var}" />`),o.trigger("submit")},Cancel:function(){$(this).dialog("close")}},close:function(){$(this).remove()}})}))}$("mi").on("click",(function(){let e=sessionStorage.getItem("mi_id");null!=e&&$("#"+t(e)).removeAttr("style"),sessionStorage.mi_id=$(this).attr("id"),n($(this)),u("true"==localStorage["option-limited-highlight"])})),$(window).scrollTop(localStorage.scroll_top);let l=sessionStorage.mi_id;null!=l&&n($("#"+t(l)))})),$((function(){let o,n;$(document).on("mouseup",(function(i){o=i.pageX,n=i.pageY,$(".select-menu").css("display","none");let[c,a,s]=function(){var t,e,o,n;let i;if(window.getSelection?i=window.getSelection():document.getSelection&&(i=document.getSelection()),null==i||"Range"!=i.type)return[void 0,void 0,void 0];let l=null===(t=null==i?void 0:i.anchorNode)||void 0===t?void 0:t.parentElement,c=null===(e=null==i?void 0:i.focusNode)||void 0===e?void 0:e.parentElement;if(null==l||null==c)return[void 0,void 0,void 0];if(0==$(l).parents(".main").length||0==$(c).parents(".main").length)return[void 0,void 0,void 0];let a,s,r,d,u=l.getBoundingClientRect(),p=c.getBoundingClientRect();return u.top<p.top||u.top==p.top&&u.left<=p.left?[a,s]=[l,c]:[a,s]=[c,l],"gd_word"==a.className?r=a.id:"gd_word"==(null===(o=a.nextElementSibling)||void 0===o?void 0:o.className)?r=a.nextElementSibling.id:console.warn("Invalid span for a source of grounding"),"gd_word"==s.className?d=s.id:"gd_word"==(null===(n=s.previousElementSibling)||void 0===n?void 0:n.className)?d=s.previousElementSibling.id:console.warn("Invalid span for a source of grounding"),[r,d,a]}();if(null==s)return;let r=sessionStorage.mi_id;null!=r&&null!=l(e($("#"+t(r))))&&$(".select-menu").css({left:o-60,top:n-50}).fadeIn(200).css("display","flex"),$(".select-menu input[type=submit]").button(),$(".select-menu .sog-add").off("click"),$(".select-menu .sog-add").on("click",(function(){$(".select-menu").css("display","none");let t={mi_id:r,start_id:c,stop_id:a};localStorage.scroll_top=$(window).scrollTop(),$.when($.post("/_add_sog",t)).done((function(){location.reload()})).fail((function(){console.error("Failed to POST _add_sog!")}))})),null!=(null==s?void 0:s.getAttribute("data-sog-mi"))?$(".select-menu .sog-del").css("display","inherit"):$(".select-menu .sog-del").css("display","none"),$(".select-menu .sog-del").off("click"),$(".select-menu .sog-del").on("click",(function(){if($(".select-menu").css("display","none"),null==s)return;let t={mi_id:s.getAttribute("data-sog-mi"),start_id:s.getAttribute("data-sog-start"),stop_id:s.getAttribute("data-sog-stop")};localStorage.scroll_top=$(window).scrollTop(),$.when($.post("/_delete_sog",t)).done((function(){location.reload()})).fail((function(){console.error("Failed to POST _delete_sog!")}))}))}))})),$((function(){$("mi").each((function(){!function(t){let o=c(e(t));null==t.data("math-concept")&&null!=o&&t.attr("mathbackground","#D3D3D3")}($(this))}))}));for(let t=1;t<10;t++)$(document).on("keydown",(function(e){var o;$("#concept-dialog")[0]||e.key==t.toString(10)&&(o=t,$("#c"+(o-1))[0]&&($('input[name="concept"]').prop("checked",!1),$("#c"+(o-1)).prop("checked",!0)))}));$(document).on("keydown",(function(t){"Enter"==t.key&&($("#concept-dialog")[0]||$("#assign-concept").trigger("click"))})),$((function(){0!=$("#error-message").text().length&&$("#error-dialog").dialog({dialogClass:"error-dialog",modal:!0,title:"Error",buttons:{OK:function(){$(this).dialog("close")}}})})),$((function(){$(window).scrollTop(localStorage.scroll_top)}))})();