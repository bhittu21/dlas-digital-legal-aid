/**
 * DLAS Voice Helpline & Telephony Intake Simulator
 * Allows judges and operators to test the real Bangla voice pipeline
 * without spending Twilio telephony minutes.
 */

(function () {
  let activeSessionId = null;
  let activeCaseId = null;
  let activeTrackingId = null;
  let currentQuestionId = "Q0";
  let currentQuestionTextBn = "";
  let isCallActive = false;
  let recognitionInstance = null;
  let isListening = false;
  let sessionAnswers = [];

  const SAMPLE_ANSWERS = {
    Q0: {
      safe: "হ্যাঁ, আমি আছি এবং আমার সমস্যা সম্পর্কে কথা বলতে সম্মত।",
      danger: "জি, আমি আছি। আমার খুব বিপদ, কথা বলতে চাই।",
      refusal: "না, আমি কোনো কথা বলব না, এটা ভুল নম্বর।",
    },
    Q1: {
      safe: "আমার পৈতৃক জমি প্রতিপক্ষ জোর করে বেদখল করেছে। কোনো যৌতুক বা শারীরিক মারধর নেই।",
      danger: "আমার স্বামী যৌতুকের জন্য আমাকে প্রতিদিন প্রচণ্ড মারধর করে এবং মেরে ফেলার হুমকি দিচ্ছে।",
    },
    Q2: {
      safe: "আমি এখন বোনের বাড়িতে নিরাপদ আশ্রয়ে আছি। সে এখানে নেই।",
      danger: "আমি একদম নিরাপদ নই, ভয়ে আছি! সে এখন দা নিয়ে আমার সামনে ঘরে বসে আছে এবং মারছে!",
    },
    Q3: {
      safe: "বাচ্চা আমার সাথেই আছে, নিরাপদে আছে। বিকেলে আমাকে ফোন দিবেন।",
      danger: "আমার ৪ বছরের সন্তানও চরম ঝুঁকিতে আছে, বাচ্চাকেও মারতে চায়! দুপুরে নিরাপদ থাকি।",
    },
  };

  let activeAudio = null;

  function stopSpeaking() {
    if (activeAudio) {
      try {
        activeAudio.pause();
        activeAudio.currentTime = 0;
      } catch (_) {}
      activeAudio = null;
    }
    if ('speechSynthesis' in window) {
      try { window.speechSynthesis.cancel(); } catch (_) {}
    }
    const wave = document.getElementById("voiceSoundwave");
    if (wave) wave.classList.remove("soundwave-active");
  }

  function fallbackSpeechSynthesis(text, onDone) {
    if (!('speechSynthesis' in window)) {
      if (onDone) onDone();
      return;
    }
    try {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = "bn-BD";
      utterance.rate = 0.95;

      const voices = window.speechSynthesis.getVoices() || [];
      const bnVoice = voices.find(v => 
        (v.lang && v.lang.toLowerCase().startsWith("bn")) || 
        (v.name && (v.name.toLowerCase().includes("bangla") || v.name.toLowerCase().includes("bengali")))
      );
      if (bnVoice) {
        utterance.voice = bnVoice;
      }

      utterance.onend = () => { if (onDone) onDone(); };
      utterance.onerror = () => { if (onDone) onDone(); };
      window.speechSynthesis.speak(utterance);
    } catch (_) {
      if (onDone) onDone();
    }
  }

  function speakBangla(text) {
    if (!text || !text.trim()) return;
    stopSpeaking();

    const wave = document.getElementById("voiceSoundwave");
    if (wave) wave.classList.add("soundwave-active");

    const onDone = () => {
      if (wave) wave.classList.remove("soundwave-active");
      activeAudio = null;
    };

    // 1. Primary: Native Bangladesh Bangla neural voice audio from backend
    try {
      const apiBase = window.DLAS_CONFIG.getApiBaseUrl();
      const ttsUrl = `${apiBase}/voice/tts?text=${encodeURIComponent(text.trim())}&lang=bn-BD`;
      const audio = new Audio(ttsUrl);
      activeAudio = audio;

      audio.onended = onDone;
      audio.onerror = () => {
        console.warn("Backend TTS stream unavailable, falling back to browser speech synthesis");
        fallbackSpeechSynthesis(text, onDone);
      };

      const playPromise = audio.play();
      if (playPromise !== undefined) {
        playPromise.catch((err) => {
          console.warn("Audio autoplay blocked or unavailable, using browser speech synthesis:", err);
          fallbackSpeechSynthesis(text, onDone);
        });
      }
    } catch (e) {
      fallbackSpeechSynthesis(text, onDone);
    }
  }

  async function renderVoiceIntakeView(container, lang) {
    container.innerHTML = `
      <div class="view-header">
        <div>
          <h1 class="view-title">${window.t("voice_title")}</h1>
          <p class="view-subtitle">${window.t("voice_subtitle")}</p>
        </div>
        <div class="view-actions">
          <span class="badge badge-outline text-xs">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
            </svg>
            16430 National Helpline Mode
          </span>
        </div>
      </div>

      <!-- Telephony Live Banner -->
      <div class="voice-sim-container">
        <div class="voice-control-panel card p-4 mb-4">
          <div class="voice-status-bar flex justify-between items-center pb-3 border-b">
            <div class="flex items-center gap-3">
              <div class="call-indicator-dot ${isCallActive ? 'call-active' : 'call-idle'}" id="callDot"></div>
              <div>
                <strong id="callStatusLabel">${isCallActive ? (lang === 'bn' ? 'কল চলছে (১৬৪৩০)' : 'Call In Progress (16430)') : (lang === 'bn' ? 'কল অপেক্ষমাণ' : 'Call Idle')}</strong>
                <span class="text-xs text-muted block" id="sessionMetaText">
                  ${activeSessionId ? `Session: ${activeSessionId} | Case: ${activeTrackingId || activeCaseId}` : (lang === 'bn' ? 'ইনবাউন্ড কল সিমুলেট করতে নিচের বোতামে চাপ দিন' : 'Click below to simulate incoming call')}
                </span>
              </div>
            </div>

            <div class="flex gap-2">
              ${!isCallActive ? `
                <button class="btn btn-success btn-sm flex items-center gap-2" id="btnStartVoiceCall">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                  </svg>
                  ${window.t("voice_start_call")}
                </button>
              ` : `
                <button class="btn btn-danger btn-sm flex items-center gap-2" id="btnEndVoiceCall">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                  ${window.t("voice_end_call")}
                </button>
              `}
            </div>
          </div>

          <!-- Active Question Speaking Box -->
          <div class="voice-prompt-box mt-4 p-4 rounded bg-slate-50 border" id="voicePromptBox" style="${isCallActive ? '' : 'opacity: 0.6; pointer-events: none;'}">
            <div class="flex items-center justify-between mb-2">
              <span class="badge badge-primary text-xs" id="activeStepBadge">
                ${currentQuestionId}: Statutory Bangla Prompt
              </span>
              <div class="soundwave-anim flex gap-1 items-end" id="voiceSoundwave">
                <span class="wave-bar"></span>
                <span class="wave-bar"></span>
                <span class="wave-bar"></span>
                <span class="wave-bar"></span>
              </div>
            </div>

            <div class="active-question-text text-lg font-medium text-slate-800" id="activePromptBn">
              ${currentQuestionTextBn || "জাতীয় আইনগত সহায়তা হেল্পলাইনে স্বাগতম। এটি একটি সরকারি আইনগত সহায়তা সেবা। আমাদের কথোপকথন রেকর্ড করা হতে পারে। যার জন্য আইনগত সহায়তা প্রয়োজন, তিনি কি এই কলে আছেন এবং নিজের সমস্যাটি সম্পর্কে কথা বলতে সম্মত?"}
            </div>

            <div class="mt-4 pt-3 border-t">
              <label class="text-xs font-semibold text-slate-600 block mb-1">
                ${window.t("voice_caller_turn")}:
              </label>
              
              <div class="flex gap-2 mb-3">
                <input type="text" class="form-input flex-1" id="inputSpokenAnswer" placeholder="কলারের উত্তর এখানে লিখুন বা মাইক্রোফোনে বলুন..." />
                <button class="btn btn-primary" id="btnSubmitSpokenAnswer">
                  ${lang === 'bn' ? 'উত্তর দাখিল করুন' : 'Submit Answer'}
                </button>
                <button class="btn btn-outline-secondary" id="btnMicInput" title="Microphone Input">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                    <line x1="12" y1="19" x2="12" y2="22"/>
                  </svg>
                </button>
              </div>

              <!-- Fast Test Buttons for Judges -->
              <div class="flex flex-wrap gap-2 text-xs">
                <span class="text-muted self-center">Judge Quick Test:</span>
                <button class="btn btn-outline-success btn-xs" id="btnSendSafeSample">
                  ✔ ${window.t("voice_btn_sample_safe")}
                </button>
                <button class="btn btn-outline-danger btn-xs" id="btnSendDangerSample">
                  ⚠ ${window.t("voice_btn_sample_danger")}
                </button>
                ${currentQuestionId === 'Q0' ? `
                  <button class="btn btn-outline-secondary btn-xs" id="btnSendRefusalSample">
                    ✖ Refusal (Abort)
                  </button>
                ` : ''}
              </div>
            </div>
          </div>
        </div>

        <!-- Incremental Persistence Feed -->
        <div class="card p-4">
          <div class="flex justify-between items-center mb-3">
            <h3 class="card-title text-base font-semibold text-slate-800">
              ${window.t("voice_answers_feed")}
            </h3>
            <span class="badge badge-success text-xs">
              ${window.t("voice_persisted_tag")}
            </span>
          </div>

          <div id="answersFeedList" class="answers-feed-list space-y-3">
            ${sessionAnswers.length === 0 ? `
              <div class="empty-state py-6 text-center text-muted">
                <p>${lang === 'bn' ? 'এখনো কোনো প্রশ্নোত্তর শুরু হয়নি। কল শুরু করুন।' : 'No turn answers recorded yet. Start a simulated call above.'}</p>
              </div>
            ` : sessionAnswers.map((ans, idx) => `
              <div class="feed-item p-3 rounded border ${ans.danger_detected ? 'border-red-400 bg-red-50' : 'bg-white'}">
                <div class="flex justify-between items-start text-xs text-muted mb-1">
                  <span class="font-bold text-slate-700">[${ans.question_id}] ${ans.question}</span>
                  <span class="badge badge-xs ${ans.danger_detected ? 'badge-danger' : 'badge-outline'}">
                    ${ans.danger_detected ? 'DANGER DETECTED' : 'SAFE'}
                  </span>
                </div>
                <div class="feed-answer text-sm text-slate-900 font-medium my-1">
                  &ldquo;${ans.answer}&rdquo;
                </div>
                <div class="flex justify-between items-center text-xs text-slate-500 mt-2 pt-1 border-t">
                  <span>Source: <code>${ans.source}</code> (Confidence: ${Math.round((ans.confidence || 1) * 100)}%)</span>
                  <span>Case ID: <code>#${ans.case_id}</code></span>
                </div>
              </div>
            `).join('')}
          </div>

          <!-- Final Case Action Banner -->
          <div id="callCompletedBanner" class="mt-4 p-4 rounded bg-emerald-50 border border-emerald-300 ${!isCallActive && activeCaseId && sessionAnswers.length > 0 ? '' : 'hidden'}">
            <div class="flex items-center justify-between">
              <div>
                <strong class="text-emerald-800 block text-base">
                  ${lang === 'bn' ? '✓ ভয়েস ইনটেক সফলভাবে সম্পন্ন হয়েছে' : '✓ Voice Intake Successfully Completed'}
                </strong>
                <span class="text-emerald-700 text-xs block">
                  ${lang === 'bn' ? 'মামলাটি PENDING_HUMAN_REVIEW অবস্থায় ড্যাশবোর্ডে যুক্ত হয়েছে।' : 'Case transitioned to PENDING_HUMAN_REVIEW and is ready for judicial review.'}
                </span>
              </div>
              <button class="btn btn-primary btn-sm" id="btnOpenCreatedCase">
                ${lang === 'bn' ? 'যাচাই প্যানেলে মামলাটি খুলুন' : 'Open Case in Review Panel'}
              </button>
            </div>
          </div>
        </div>
      </div>
    `;

    // Bind Event Listeners
    const btnStart = document.getElementById("btnStartVoiceCall");
    if (btnStart) {
      btnStart.addEventListener("click", async () => {
        try {
          const res = await window.dlasApi.startVoiceSimulation("+8801711223344", "সুলতানা রহমান", "Dhaka");
          activeSessionId = res.session_id;
          activeCaseId = res.case_id;
          activeTrackingId = res.tracking_id;
          currentQuestionId = "Q0";
          currentQuestionTextBn = res.prompt_text_bn;
          isCallActive = true;
          sessionAnswers = [];
          renderVoiceIntakeView(container, lang);
          speakBangla(currentQuestionTextBn);
        } catch (err) {
          window.notify(err.message, "error");
        }
      });
    }

    const btnEnd = document.getElementById("btnEndVoiceCall");
    if (btnEnd) {
      btnEnd.addEventListener("click", () => {
        isCallActive = false;
        stopSpeaking();
        renderVoiceIntakeView(container, lang);
        window.notify("Voice intake call ended.", "info");
      });
    }

    const btnSubmit = document.getElementById("btnSubmitSpokenAnswer");
    const inputAnswer = document.getElementById("inputSpokenAnswer");
    if (btnSubmit && inputAnswer) {
      btnSubmit.addEventListener("click", async () => {
        const text = inputAnswer.value.trim();
        if (!text) return;
        await submitStep(text, container, lang);
      });
      inputAnswer.addEventListener("keypress", async (e) => {
        if (e.key === "Enter") {
          const text = inputAnswer.value.trim();
          if (text) await submitStep(text, container, lang);
        }
      });
    }

    // Quick Sample Buttons
    const btnSafe = document.getElementById("btnSendSafeSample");
    if (btnSafe) {
      btnSafe.addEventListener("click", async () => {
        const sample = SAMPLE_ANSWERS[currentQuestionId]?.safe || "হ্যাঁ, আমি সম্মত।";
        await submitStep(sample, container, lang);
      });
    }

    const btnDanger = document.getElementById("btnSendDangerSample");
    if (btnDanger) {
      btnDanger.addEventListener("click", async () => {
        const sample = SAMPLE_ANSWERS[currentQuestionId]?.danger || "আমার স্বামী দা নিয়ে আমাকে মারধর করছে, চরম বিপদে আছি!";
        await submitStep(sample, container, lang);
      });
    }

    const btnRefusal = document.getElementById("btnSendRefusalSample");
    if (btnRefusal) {
      btnRefusal.addEventListener("click", async () => {
        const sample = SAMPLE_ANSWERS.Q0.refusal;
        await submitStep(sample, container, lang);
      });
    }

    // Speech Recognition (Microphone)
    const btnMic = document.getElementById("btnMicInput");
    if (btnMic) {
      btnMic.addEventListener("click", () => {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRec) {
          window.notify("Web SpeechRecognition is not supported in this browser. Please type the answer.", "warning");
          return;
        }

        if (isListening) {
          if (recognitionInstance) recognitionInstance.stop();
          isListening = false;
          btnMic.classList.remove("btn-danger");
          return;
        }

        recognitionInstance = new SpeechRec();
        recognitionInstance.lang = "bn-BD";
        recognitionInstance.interimResults = false;
        recognitionInstance.maxAlternatives = 1;

        recognitionInstance.onstart = () => {
          isListening = true;
          btnMic.classList.add("btn-danger");
          window.notify("Listening (Bangla)... Speak now.", "info");
        };

        recognitionInstance.onresult = (e) => {
          const transcript = e.results[0][0].transcript;
          if (inputAnswer) inputAnswer.value = transcript;
        };

        recognitionInstance.onerror = (e) => {
          window.notify("Speech recognition error: " + e.error, "error");
          isListening = false;
          btnMic.classList.remove("btn-danger");
        };

        recognitionInstance.onend = () => {
          isListening = false;
          btnMic.classList.remove("btn-danger");
        };

        recognitionInstance.start();
      });
    }

    // Open Created Case in Review Panel
    const btnOpenCase = document.getElementById("btnOpenCreatedCase");
    if (btnOpenCase && activeCaseId) {
      btnOpenCase.addEventListener("click", () => {
        window.dlasStore.setState({ activeCaseId: activeCaseId, activeView: "detail" });
      });
    }
  }

  async function submitStep(spokenAnswer, container, lang) {
    if (!activeSessionId) {
      window.notify("No active voice call session.", "error");
      return;
    }

    try {
      const res = await window.dlasApi.submitVoiceStep(
        activeSessionId,
        currentQuestionId,
        spokenAnswer,
        "BROWSER_SIMULATED",
        0.96
      );

      // Add to feed immediately
      sessionAnswers.push(res.persisted_answer);

      if (res.danger_detected) {
        window.notify(`⚠️ Danger Alert: ${res.risk_flags.join(", ")}`, "warning");
      }

      if (res.is_call_completed) {
        isCallActive = false;
        window.notify(res.message_bn, "success");
        speakBangla(lang === 'bn' ? "আপনার আবেদনটি সফলভাবে সংরক্ষিত হয়েছে। ধন্যবাদ।" : "Your legal aid intake is complete. Thank you.");
      } else {
        currentQuestionId = res.next_step;
        currentQuestionTextBn = res.next_prompt_text_bn || "";
        speakBangla(currentQuestionTextBn);
      }

      renderVoiceIntakeView(container, lang);
    } catch (err) {
      window.notify(err.message, "error");
    }
  }

  window.renderVoiceIntakeView = renderVoiceIntakeView;
})();
