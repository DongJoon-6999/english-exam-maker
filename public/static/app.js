// English Summary Problem Generator Client Logic

document.addEventListener('DOMContentLoaded', () => {
  // Lucide icons initialization
  if (window.lucide) {
    lucide.createIcons();
  }

  // State
  let state = {
    provider: localStorage.getItem('esp_provider') || 'gemini',
    geminiKey: localStorage.getItem('esp_gemini_key') || '',
    claudeKey: localStorage.getItem('esp_claude_key') || '',
    openaiKey: localStorage.getItem('esp_openai_key') || '',
    geminiModel: localStorage.getItem('esp_gemini_model') || 'gemini-3.6-flash',
    claudeModel: localStorage.getItem('esp_claude_model') || 'claude-3-7-sonnet-20250219',
    openaiModel: localStorage.getItem('esp_openai_model') || 'gpt-4o-mini',
    candidateCount: 3,
    difficulty: 'basic',
    serverKeys: { gemini: false, claude: false, openai: false },
    samples: [],
    candidates: [],
    activeCandidateIndex: 0
  };

  // DOM Elements
  const passageInput = document.getElementById('passage-input');
  const passageCharCount = document.getElementById('passage-char-count');
  const targetGrammarInput = document.getElementById('target-grammar-input');
  const targetVocabInput = document.getElementById('target-vocab-input');
  const presetSelector = document.getElementById('preset-selector');
  const btnGenerate = document.getElementById('btn-generate');
  const placeholderView = document.getElementById('placeholder-view');
  const loadingView = document.getElementById('loading-view');
  const resultView = document.getElementById('result-view');
  const candidateTabs = document.getElementById('candidate-tabs');
  const btnTrySample = document.getElementById('btn-try-sample');
  const difficultyDesc = document.getElementById('difficulty-desc');

  // Card Elements
  const badgeGrammar = document.getElementById('badge-grammar');
  const badgeTheme = document.getElementById('badge-theme');
  const cardDirection = document.getElementById('card-direction');
  const cardSentenceDisplay = document.getElementById('card-sentence-display');
  const cardGivenWords = document.getElementById('card-given-words');
  const cardConditions = document.getElementById('card-conditions');
  const functionalWordsChips = document.getElementById('functional-words-chips');
  const functionalWordsPanel = document.getElementById('functional-words-panel');
  
  // Student Solve Elements
  const studentAnswerInput = document.getElementById('student-answer-input');
  const btnCheckStudentAnswer = document.getElementById('btn-check-student-answer');
  const studentEvalResult = document.getElementById('student-eval-result');

  // Teacher Answer Elements
  const btnToggleAnswer = document.getElementById('btn-toggle-answer');
  const answerContent = document.getElementById('answer-content');
  const answerChevron = document.getElementById('answer-chevron');
  const ansBlank = document.getElementById('ans-blank');
  const ansFullSentence = document.getElementById('ans-full-sentence');
  const ansTranslation = document.getElementById('ans-translation');
  const ansAddedWords = document.getElementById('ans-added-words');
  const ansModifiedWords = document.getElementById('ans-modified-words');
  const ansExplanation = document.getElementById('ans-explanation');

  // Copy Action Buttons
  const btnCopyHwp = document.getElementById('btn-copy-hwp');
  const btnCopyStudent = document.getElementById('btn-copy-student');
  const btnCopyFull = document.getElementById('btn-copy-full');
  const btnPrintView = document.getElementById('btn-print-view');

  // Settings Modal Elements
  const btnOpenSettings = document.getElementById('btn-open-settings');
  const btnCloseSettings = document.getElementById('btn-close-settings');
  const settingsModal = document.getElementById('settings-modal');
  const currentProviderBadge = document.getElementById('current-provider-badge');
  const providerButtons = document.querySelectorAll('.provider-btn');
  const modelSelect = document.getElementById('model-select');
  const apiKeyInput = document.getElementById('api-key-input');
  const apiKeyLabel = document.getElementById('api-key-label');
  const apiKeyHelpLink = document.getElementById('api-key-help-link');
  const btnTestKey = document.getElementById('btn-test-key');
  const testKeyStatus = document.getElementById('test-key-status');
  const btnSaveSettings = document.getElementById('btn-save-settings');

  // Toast
  const toast = document.getElementById('toast');
  const toastMessage = document.getElementById('toast-message');

  // 1. Initial Load & Setup
  fetch('/api/config-status')
    .then(res => res.json())
    .then(data => {
      state.serverKeys = data.server_keys || {};
      updateProviderBadge();
    })
    .catch(() => updateProviderBadge());

  function updateProviderBadge() {
    if (state.provider === 'gemini') {
      currentProviderBadge.innerHTML = '<span class="text-indigo-600 font-bold">Gemini AI</span>';
    } else if (state.provider === 'claude') {
      currentProviderBadge.innerHTML = '<span class="text-indigo-600 font-bold">Claude AI</span>';
    } else if (state.provider === 'openai') {
      currentProviderBadge.innerHTML = '<span class="text-indigo-600 font-bold">OpenAI GPT</span>';
    } else {
      currentProviderBadge.innerHTML = '<span class="text-slate-600 font-medium">모의(Mock) 모드</span>';
    }
  }
  updateProviderBadge();

  // Load sample passages from server
  fetch('/api/sample-passages')
    .then(res => res.json())
    .then(data => {
      state.samples = data.samples || [];
      presetSelector.innerHTML = '<option value="">-- 예시 지문 선택 --</option>';
      state.samples.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.id;
        opt.textContent = s.title;
        presetSelector.appendChild(opt);
      });
    })
    .catch(err => console.error('Failed to load samples:', err));

  // Character counter
  passageInput.addEventListener('input', () => {
    passageCharCount.textContent = passageInput.value.length;
  });

  // Preset Selector handler
  presetSelector.addEventListener('change', () => {
    const selectedId = presetSelector.value;
    const sample = state.samples.find(s => s.id === selectedId);
    if (sample) {
      passageInput.value = sample.passage.trim();
      targetGrammarInput.value = sample.grammar_hint || '';
      targetVocabInput.value = sample.vocab_hint || '';
      passageCharCount.textContent = passageInput.value.length;
    }
  });

  // Try sample button in placeholder
  btnTrySample.addEventListener('click', () => {
    if (state.samples.length > 0) {
      const sample = state.samples[0];
      presetSelector.value = sample.id;
      passageInput.value = sample.passage.trim();
      targetGrammarInput.value = sample.grammar_hint || '';
      targetVocabInput.value = sample.vocab_hint || '';
      passageCharCount.textContent = passageInput.value.length;
      btnGenerate.click();
    }
  });

  // Grammar quick pills
  document.querySelectorAll('.grammar-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      const text = pill.textContent.replace('+', '').trim();
      const current = targetGrammarInput.value.trim();
      if (!current) {
        targetGrammarInput.value = text;
      } else if (!current.includes(text)) {
        targetGrammarInput.value = `${current}, ${text}`;
      }
    });
  });

  // Difficulty toggle buttons
  const diffDescMap = {
    intro: '고1 기초 (풍부한 문맥 힌트)',
    basic: '고1~고2 표준 내신',
    advanced: '고2~고3 3점 심화',
    killer: '고3/수능 1등급 변별'
  };
  const diffBtns = document.querySelectorAll('.difficulty-btn');
  diffBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      diffBtns.forEach(b => {
        b.classList.remove('active', 'bg-white', 'text-indigo-600', 'shadow-sm', 'font-bold');
        b.classList.add('text-slate-600', 'font-medium');
        const sub = b.querySelector('span:last-child');
        if (sub) {
          sub.classList.remove('text-indigo-400');
          sub.classList.add('text-slate-400');
        }
      });
      btn.classList.add('active', 'bg-white', 'text-indigo-600', 'shadow-sm', 'font-bold');
      btn.classList.remove('text-slate-600', 'font-medium');
      const activeSub = btn.querySelector('span:last-child');
      if (activeSub) {
        activeSub.classList.remove('text-slate-400');
        activeSub.classList.add('text-indigo-400');
      }

      state.difficulty = btn.dataset.diff;
      if (difficultyDesc) {
        difficultyDesc.textContent = diffDescMap[state.difficulty] || '고1~고2 표준 내신';
      }
    });
  });

  // Candidate Count toggle buttons
  const countBtns = document.querySelectorAll('.count-btn');
  countBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      countBtns.forEach(b => {
        b.classList.remove('active', 'bg-white', 'text-indigo-600', 'shadow-sm', 'font-bold');
        b.classList.add('text-slate-600', 'font-medium');
      });
      btn.classList.add('active', 'bg-white', 'text-indigo-600', 'shadow-sm', 'font-bold');
      btn.classList.remove('text-slate-600', 'font-medium');
      state.candidateCount = parseInt(btn.dataset.count, 10);
    });
  });

  // 2. Generate Problems
  btnGenerate.addEventListener('click', async () => {
    const passage = passageInput.value.trim();
    if (!passage || passage.length < 20) {
      showToast('지문을 최소 20자 이상 입력해 주세요.', true);
      passageInput.focus();
      return;
    }

    // Determine API Key
    let key = '';
    let model = '';
    if (state.provider === 'gemini') {
      key = state.geminiKey;
      model = state.geminiModel;
    } else if (state.provider === 'claude') {
      key = state.claudeKey;
      model = state.claudeModel;
    } else if (state.provider === 'openai') {
      key = state.openaiKey;
      model = state.openaiModel;
    }

    // UI state transition to Loading
    placeholderView.classList.add('hidden');
    resultView.classList.add('hidden');
    loadingView.classList.remove('hidden');
    btnGenerate.disabled = true;

    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          passage: passage,
          target_grammar: targetGrammarInput.value.trim(),
          target_vocab: targetVocabInput.value.trim(),
          provider: state.provider,
          api_key: key,
          model_name: model,
          candidate_count: state.candidateCount,
          difficulty: state.difficulty
        })
      });

      const resData = await response.json();
      if (!response.ok) {
        throw new Error(resData.detail || '문제 생성에 실패했습니다.');
      }

      state.candidates = resData.data.candidates || [];
      if (state.candidates.length === 0) {
        throw new Error('생성된 문제가 없습니다.');
      }

      // Initialize functional words detail & state for each candidate
      state.candidates.forEach(cand => {
        if (!Array.isArray(cand.functional_words_detail) || cand.functional_words_detail.length === 0) {
          const added = Array.isArray(cand.added_functional_words) ? cand.added_functional_words : [];
          cand.functional_words_detail = added.map(w => ({
            word: w,
            role: '어법 기능어',
            omitted_from_given: true,
            reason: '어법상 필수 기능어'
          }));
        }
        if (!cand.original_given_words) {
          cand.original_given_words = Array.isArray(cand.given_words) ? [...cand.given_words] : [];
        }
        applyCandidateFunctionalWords(cand);
      });

      state.activeCandidateIndex = 0;
      renderCandidateTabs();
      renderActiveCandidate();

      loadingView.classList.add('hidden');
      resultView.classList.remove('hidden');
      resultView.classList.add('flex');

      if (resData.provider === 'gemini') {
        showToast('Gemini AI로 서술형 요약 문제가 성공적으로 생성되었습니다!');
      } else if (resData.provider === 'claude') {
        showToast('Claude AI로 서술형 요약 문제가 성공적으로 생성되었습니다!');
      } else if (resData.provider === 'openai') {
        showToast('OpenAI로 서술형 요약 문제가 성공적으로 생성되었습니다!');
      } else {
        showToast('서술형 요약 문제가 성공적으로 생성되었습니다!');
      }

    } catch (err) {
      loadingView.classList.add('hidden');
      placeholderView.classList.remove('hidden');
      alert(`오류 발생: ${err.message}`);
    } finally {
      btnGenerate.disabled = false;
      if (window.lucide) lucide.createIcons();
    }
  });

  // 3. Render Candidate Tabs
  function renderCandidateTabs() {
    candidateTabs.innerHTML = '';
    state.candidates.forEach((cand, idx) => {
      const btn = document.createElement('button');
      btn.className = `candidate-tab px-3 py-1.5 text-xs font-semibold rounded-lg transition ${idx === state.activeCandidateIndex ? 'active' : 'text-slate-600 bg-slate-100 hover:bg-slate-200'}`;
      btn.textContent = `후보 ${idx + 1} (${cand.target_grammar_used ? cand.target_grammar_used.slice(0, 10) + '...' : '유형 ' + (idx + 1)})`;
      btn.addEventListener('click', () => {
        state.activeCandidateIndex = idx;
        renderCandidateTabs();
        renderActiveCandidate();
      });
      candidateTabs.appendChild(btn);
    });
  }

  // 4. Candidate Functional Words Synchronization
  function applyCandidateFunctionalWords(cand) {
    let currentGiven = [...(cand.original_given_words || cand.given_words || [])];
    let remainingOmitted = [];

    if (Array.isArray(cand.functional_words_detail)) {
      cand.functional_words_detail.forEach(f => {
        if (!f.omitted_from_given) {
          // Included in <보기>
          if (!currentGiven.includes(f.word)) {
            currentGiven.push(f.word);
          }
        } else {
          // Omitted from <보기> (student must deduce)
          currentGiven = currentGiven.filter(w => w !== f.word);
          if (!remainingOmitted.includes(f.word)) {
            remainingOmitted.push(f.word);
          }
        }
      });
    }

    cand.current_given_words = currentGiven;
    cand.current_added_words = remainingOmitted;

    if (remainingOmitted.length > 0) {
      cand.current_conditions = [
        `1. 어법상 기능어 반드시 추가할 것`,
        `2. 필요시 단어를 변형할 것 (수일치, 시제, 분사, 품사 변형 등)`
      ];
    } else {
      cand.current_conditions = [
        `1. <보기>에 주어진 단어만을 모두 활용할 것 (단어 추가 없음)`,
        `2. 필요시 단어를 변형할 것 (수일치, 시제, 분사, 품사 변형 등)`
      ];
    }
  }

  // 5. Render Active Candidate Card
  function renderActiveCandidate() {
    const cand = state.candidates[state.activeCandidateIndex];
    if (!cand) return;

    applyCandidateFunctionalWords(cand);

    badgeGrammar.textContent = cand.target_grammar_used || '핵심 문법';
    badgeTheme.textContent = cand.theme_title || '요약문';
    cardDirection.textContent = cand.direction || '■ 윗글의 내용을 한 문장으로 요약하고자 한다. <보기>에 주어진 단어를 활용하여 빈칸 (A)에 들어갈 말을 영어로 쓰시오. (단, <조건>에 맞게 쓸 것)';

    // Summary Sentence with shaded blank
    const prefix = cand.sentence_prefix || '';
    const suffix = cand.sentence_suffix || '';
    
    // In student preview view, we render the blank placeholder with (A)
    cardSentenceDisplay.innerHTML = `
      <span>${escapeHtml(prefix)}</span>
      <span class="blank-highlight mx-1 font-semibold text-indigo-900 border-b-2 border-indigo-700 bg-indigo-50/80 px-2 py-0.5 rounded">
        (A) [ <span class="text-slate-400 font-normal italic">____________________________________</span> ]
      </span>
      <span>${escapeHtml(suffix)}</span>
    `;

    // Render Functional Words Chips
    renderFunctionalWordsChips(cand);

    // Given Words
    const words = Array.isArray(cand.current_given_words) ? cand.current_given_words.join(' / ') : (cand.current_given_words || '');
    cardGivenWords.textContent = words;

    // Conditions
    cardConditions.innerHTML = '';
    const conditions = Array.isArray(cand.current_conditions) ? cand.current_conditions : [
      '1. 어법상 기능어 반드시 추가할 것',
      '2. 필요시 단어를 변형할 것'
    ];
    conditions.forEach(cond => {
      const li = document.createElement('li');
      li.textContent = cond.replace(/^\d+\.\s*/, '');
      cardConditions.appendChild(li);
    });

    // Reset student practice sandbox
    studentAnswerInput.value = '';
    studentEvalResult.classList.add('hidden');

    // Teacher Guide / Answers
    ansBlank.textContent = cand.blank_answer || '';
    ansFullSentence.textContent = cand.full_sentence || (prefix + cand.blank_answer + suffix);
    ansTranslation.textContent = cand.translation_korean || '';

    // Added words
    const added = Array.isArray(cand.current_added_words) && cand.current_added_words.length > 0 ? cand.current_added_words.join(', ') : '없음 (보기 단어 모두 제공)';
    ansAddedWords.textContent = added;

    // Modified words
    ansModifiedWords.innerHTML = '';
    if (Array.isArray(cand.modified_words) && cand.modified_words.length > 0) {
      cand.modified_words.forEach(item => {
        const row = document.createElement('div');
        row.className = 'text-xs text-slate-700 font-mono';
        row.innerHTML = `<span class="text-slate-400 font-sans">원형:</span> <strong class="text-slate-900">${escapeHtml(item.base)}</strong> → <span class="text-slate-400 font-sans">변형:</span> <strong class="text-amber-700">${escapeHtml(item.modified)}</strong> <span class="text-[11px] text-slate-500 font-sans">(${escapeHtml(item.reason || '')})</span>`;
        ansModifiedWords.appendChild(row);
      });
    } else {
      ansModifiedWords.innerHTML = '<span class="text-slate-500">변형 없음 (단어 원형 그대로 활용)</span>';
    }

    ansExplanation.textContent = cand.grammar_explanation || '';

    if (window.lucide) lucide.createIcons();
  }

  // 6. Render Functional Words Interactive Chips
  function renderFunctionalWordsChips(cand) {
    if (!functionalWordsChips) return;
    functionalWordsChips.innerHTML = '';

    const list = cand.functional_words_detail || [];
    if (list.length === 0) {
      functionalWordsChips.innerHTML = '<span class="text-xs text-slate-500">감지된 기능어가 없습니다.</span>';
      return;
    }

    list.forEach((item, fIdx) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      const isIncluded = !item.omitted_from_given;

      if (isIncluded) {
        btn.className = 'inline-flex items-center space-x-1.5 px-3 py-1 text-xs font-semibold rounded-lg bg-indigo-600 text-white shadow-sm hover:bg-indigo-700 transition cursor-pointer';
        btn.innerHTML = `
          <i data-lucide="check-square" class="w-3.5 h-3.5"></i>
          <span>${escapeHtml(item.word)}</span>
          <span class="text-[10px] text-indigo-200">(${escapeHtml(item.role || '기능어')})</span>
          <span class="text-[10px] bg-indigo-800/60 px-1 py-0.2 rounded text-indigo-100 font-normal">보기제공됨</span>
        `;
      } else {
        btn.className = 'inline-flex items-center space-x-1.5 px-3 py-1 text-xs font-medium rounded-lg bg-white border border-slate-300 text-slate-700 hover:border-indigo-500 hover:text-indigo-600 shadow-sm transition cursor-pointer';
        btn.innerHTML = `
          <i data-lucide="square" class="w-3.5 h-3.5 text-slate-400"></i>
          <span class="font-bold">${escapeHtml(item.word)}</span>
          <span class="text-[10px] text-slate-500">(${escapeHtml(item.role || '기능어')})</span>
          <span class="text-[10px] bg-amber-100 px-1 py-0.2 rounded text-amber-800 font-medium">학생유추(제외)</span>
        `;
      }

      btn.addEventListener('click', () => {
        item.omitted_from_given = !item.omitted_from_given;
        applyCandidateFunctionalWords(cand);
        renderActiveCandidate();
        showToast(isIncluded ? `'${item.word}' 단어를 조건으로 뺐습니다 (난이도 상승).` : `'${item.word}' 단어를 <보기>에 추가했습니다 (난이도 하향).`);
      });

      functionalWordsChips.appendChild(btn);
    });

    if (window.lucide) lucide.createIcons();
  }

  // 7. Student Practice Sandbox Evaluation
  btnCheckStudentAnswer.addEventListener('click', () => {
    const cand = state.candidates[state.activeCandidateIndex];
    if (!cand) return;

    const studentInput = studentAnswerInput.value.trim();
    if (!studentInput) {
      showToast('답안을 입력해 주세요.', true);
      return;
    }

    const clean = s => s.toLowerCase().replace(/[.,!?;:]/g, '').replace(/\s+/g, ' ').trim();
    const isExact = clean(studentInput) === clean(cand.blank_answer);

    studentEvalResult.classList.remove('hidden');
    if (isExact) {
      studentEvalResult.className = 'text-xs p-3 rounded-lg bg-emerald-100 text-emerald-900 border border-emerald-300 font-medium';
      studentEvalResult.innerHTML = `🎉 <strong>정답입니다!</strong> 완벽하게 조건을 적용하여 영작했습니다.`;
    } else {
      studentEvalResult.className = 'text-xs p-3 rounded-lg bg-amber-50 text-amber-900 border border-amber-300 space-y-1';
      studentEvalResult.innerHTML = `
        <div class="font-bold text-amber-800">⚠️ 아쉽게도 정답과 일치하지 않습니다.</div>
        <div><strong>입력한 답안:</strong> ${escapeHtml(studentInput)}</div>
        <div><strong>모범 정답:</strong> <span class="font-bold text-indigo-700 font-mono">${escapeHtml(cand.blank_answer)}</span></div>
      `;
    }
  });

  // 8. Toggle Teacher Answer Collapsible
  btnToggleAnswer.addEventListener('click', () => {
    answerContent.classList.toggle('hidden');
    if (answerContent.classList.contains('hidden')) {
      answerChevron.style.transform = 'rotate(0deg)';
    } else {
      answerChevron.style.transform = 'rotate(180deg)';
    }
  });

  // 9. Clipboard Copy Actions
  // 9.1 HWP Formatted Rich Copy
  btnCopyHwp.addEventListener('click', async () => {
    const cand = state.candidates[state.activeCandidateIndex];
    if (!cand) return;

    const wordsStr = Array.isArray(cand.current_given_words) ? cand.current_given_words.join(' / ') : cand.given_words;
    const condList = Array.isArray(cand.current_conditions) ? cand.current_conditions.map((c, i) => `${i+1}. ${c.replace(/^\d+\.\s*/, '')}`).join('<br>') : '1. 어법상 기능어 반드시 추가할 것<br>2. 필요시 단어를 변형할 것';
    
    // HTML table structure that pastes beautifully into Hancom Hangul (HWP) & MS Word
    const htmlSnippet = `
      <div style="font-family: 'Batang', 'Malgun Gothic', serif; font-size: 11pt; line-height: 1.6; color: #000;">
        <p style="font-weight: bold; margin-bottom: 8px;">${escapeHtml(cand.direction)}</p>
        
        <table border="1" cellspacing="0" cellpadding="8" style="width: 100%; border: 1.5pt solid #000000; border-collapse: collapse; margin-bottom: 12px;">
          <tr>
            <td style="padding: 12px; font-size: 11pt; line-height: 1.8;">
              ${escapeHtml(cand.sentence_prefix)} <u>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(A)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</u> ${escapeHtml(cand.sentence_suffix)}
              
              <div style="margin-top: 14px; padding-top: 10px; border-top: 0.5pt solid #888888;">
                <p style="margin: 0 0 4px 0; font-weight: bold;">&lt;단어&gt;</p>
                <p style="margin: 0 0 8px 0; font-family: 'Times New Roman', serif;">${escapeHtml(wordsStr)}</p>
                
                <p style="margin: 0 0 4px 0; font-weight: bold;">&lt;조건&gt;</p>
                <div style="margin: 0;">${condList}</div>
              </div>
            </td>
          </tr>
        </table>
      </div>
    `;

    const plainSnippet = `■ 윗글의 내용을 한 문장으로 요약하고자 한다. <보기>에 주어진 단어를 활용하여 빈칸 (A)에 들어갈 말을 영어로 쓰시오. (단, <조건>에 맞게 쓸 것)\n\n` +
      `${cand.sentence_prefix} [ (A) ________________________________ ] ${cand.sentence_suffix}\n\n` +
      `<단어>\n${wordsStr}\n\n` +
      `<조건>\n` +
      (Array.isArray(cand.current_conditions) ? cand.current_conditions.map((c, i) => `${i+1}. ${c.replace(/^\d+\.\s*/, '')}`).join('\n') : '') + '\n';

    copyRichText(htmlSnippet, plainSnippet, '한글(HWP)/Word용 표 서식이 복사되었습니다!');
  });

  // 9.2 Student Problem Only Plain Text Copy
  btnCopyStudent.addEventListener('click', () => {
    const cand = state.candidates[state.activeCandidateIndex];
    if (!cand) return;

    const wordsStr = Array.isArray(cand.current_given_words) ? cand.current_given_words.join(' / ') : cand.given_words;
    const condStr = Array.isArray(cand.current_conditions) ? cand.current_conditions.map((c, i) => `${i+1}. ${c.replace(/^\d+\.\s*/, '')}`).join('\n') : '';

    const text = `${cand.direction}\n\n` +
      `[요약문]\n${cand.sentence_prefix} (A) [ ________________________________ ] ${cand.sentence_suffix}\n\n` +
      `<단어>\n${wordsStr}\n\n` +
      `<조건>\n${condStr}\n`;

    copyPlainText(text, '학생용 문제가 복사되었습니다!');
  });

  // 9.3 Full Problem & Answer Copy
  btnCopyFull.addEventListener('click', () => {
    const cand = state.candidates[state.activeCandidateIndex];
    if (!cand) return;

    const wordsStr = Array.isArray(cand.current_given_words) ? cand.current_given_words.join(' / ') : cand.given_words;
    const condStr = Array.isArray(cand.current_conditions) ? cand.current_conditions.map((c, i) => `${i+1}. ${c.replace(/^\d+\.\s*/, '')}`).join('\n') : '';
    const addedStr = Array.isArray(cand.current_added_words) && cand.current_added_words.length > 0 ? cand.current_added_words.join(', ') : '없음 (보기 단어 모두 제공)';
    const modStr = Array.isArray(cand.modified_words) ? cand.modified_words.map(m => `${m.base} → ${m.modified} (${m.reason || ''})`).join('\n') : '변형 없음';

    const text = `================ [문제지] ================\n` +
      `${cand.direction}\n\n` +
      `[요약문]\n${cand.sentence_prefix} (A) [ ________________________________ ] ${cand.sentence_suffix}\n\n` +
      `<단어>\n${wordsStr}\n\n` +
      `<조건>\n${condStr}\n\n` +
      `================ [정답 및 해설] ================\n` +
      `【빈칸 (A) 정답】: ${cand.blank_answer}\n\n` +
      `【완성 문장】: ${cand.full_sentence || (cand.sentence_prefix + cand.blank_answer + cand.sentence_suffix)}\n\n` +
      `【요약문 해석】: ${cand.translation_korean}\n\n` +
      `【추가된 기능어】: ${addedStr}\n\n` +
      `【단어 변형】:\n${modStr}\n\n` +
      `【문법 및 출제 포인트】:\n${cand.grammar_explanation}\n`;

    copyPlainText(text, '정답 및 해설을 포함한 전체 내용이 복사되었습니다!');
  });

  // 9.4 Print View
  btnPrintView.addEventListener('click', () => {
    if (state.candidates.length === 0) {
      showToast('먼저 문제를 생성해 주세요.', true);
      return;
    }
    window.print();
  });

  // 10. Settings Modal Logic
  btnOpenSettings.addEventListener('click', () => {
    providerButtons.forEach(btn => {
      if (btn.dataset.provider === state.provider) {
        btn.classList.add('active', 'border-indigo-600', 'bg-indigo-50', 'text-indigo-700', 'font-bold');
        btn.classList.remove('border-slate-200', 'bg-slate-50', 'text-slate-700');
      } else {
        btn.classList.remove('active', 'border-indigo-600', 'bg-indigo-50', 'text-indigo-700', 'font-bold');
        btn.classList.add('border-slate-200', 'bg-slate-50', 'text-slate-700');
      }
    });

    updateModelAndKeyInputs();
    testKeyStatus.textContent = '';
    settingsModal.classList.remove('hidden');
  });

  btnCloseSettings.addEventListener('click', () => {
    settingsModal.classList.add('hidden');
  });

  providerButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      providerButtons.forEach(b => {
        b.classList.remove('active', 'border-indigo-600', 'bg-indigo-50', 'text-indigo-700', 'font-bold');
        b.classList.add('border-slate-200', 'bg-slate-50', 'text-slate-700');
      });
      btn.classList.add('active', 'border-indigo-600', 'bg-indigo-50', 'text-indigo-700', 'font-bold');
      btn.classList.remove('border-slate-200', 'bg-slate-50', 'text-slate-700');
      
      const prov = btn.dataset.provider;
      updateModelAndKeyInputs(prov);
    });
  });

  function getSelectedModalProvider() {
    const active = document.querySelector('.provider-btn.active');
    return active ? active.dataset.provider : 'gemini';
  }

  function updateModelAndKeyInputs(selectedProv) {
    const prov = selectedProv || getSelectedModalProvider();
    const modelSelectGroup = document.getElementById('model-select-group');
    const apiKeyGroup = document.getElementById('api-key-group');

    if (prov === 'gemini') {
      modelSelectGroup.style.display = 'block';
      apiKeyGroup.style.display = 'block';
      modelSelect.innerHTML = `
        <option value="gemini-3.6-flash">Gemini 3.6 Flash (권장, 최신 플래그십)</option>
        <option value="gemini-2.0-flash">Gemini 2.0 Flash (빠른 속도)</option>
        <option value="gemini-1.5-flash">Gemini 1.5 Flash (표준)</option>
        <option value="gemini-1.5-pro">Gemini 1.5 Pro (고심도 추론)</option>
      `;
      modelSelect.value = state.geminiModel || 'gemini-3.6-flash';
      apiKeyLabel.innerHTML = 'Gemini API Key <span class="text-[11px] font-normal text-emerald-600 font-sans">(기본 연동됨 - 비워두셔도 자동 작동)</span>';
      apiKeyHelpLink.href = 'https://aistudio.google.com/app/apikey';
      apiKeyHelpLink.style.display = 'flex';
      apiKeyInput.value = state.geminiKey || '';
      apiKeyInput.placeholder = '기본 AI 키 연동됨 (개인 키로 변경 시에만 입력)';
    } else if (prov === 'claude') {
      modelSelectGroup.style.display = 'block';
      apiKeyGroup.style.display = 'block';
      modelSelect.innerHTML = `
        <option value="claude-3-7-sonnet-20250219">Claude 3.7 Sonnet (권장, 최신 플래그십 모델)</option>
        <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet (고품질 문제 생성)</option>
        <option value="claude-3-5-haiku-20241022">Claude 3.5 Haiku (초고속 & 경제적)</option>
      `;
      modelSelect.value = state.claudeModel || 'claude-3-7-sonnet-20250219';
      apiKeyLabel.textContent = 'Claude (Anthropic) API Key';
      apiKeyHelpLink.href = 'https://console.anthropic.com/settings/keys';
      apiKeyHelpLink.style.display = 'flex';
      apiKeyInput.value = state.claudeKey || '';
      apiKeyInput.placeholder = 'sk-ant-api...';
    } else if (prov === 'openai') {
      modelSelectGroup.style.display = 'block';
      apiKeyGroup.style.display = 'block';
      modelSelect.innerHTML = `
        <option value="gpt-4o-mini">GPT-4o-mini (빠르고 경제적)</option>
        <option value="gpt-4o">GPT-4o (최고 성능)</option>
      `;
      modelSelect.value = state.openaiModel || 'gpt-4o-mini';
      apiKeyLabel.textContent = 'OpenAI API Key';
      apiKeyHelpLink.href = 'https://platform.openai.com/api-keys';
      apiKeyHelpLink.style.display = 'flex';
      apiKeyInput.value = state.openaiKey || '';
      apiKeyInput.placeholder = 'sk-...';
    } else {
      modelSelectGroup.style.display = 'none';
      apiKeyGroup.style.display = 'none';
    }
  }

  // Test Key button in settings
  btnTestKey.addEventListener('click', async () => {
    const prov = getSelectedModalProvider();
    if (prov === 'mock') {
      testKeyStatus.className = 'text-xs font-semibold text-emerald-600';
      testKeyStatus.textContent = '모의 모드는 키가 필요 없습니다.';
      return;
    }

    const key = apiKeyInput.value.trim();

    testKeyStatus.className = 'text-xs font-medium text-slate-500';
    testKeyStatus.textContent = '연결 확인 중...';

    try {
      const resp = await fetch('/api/test-key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: prov,
          api_key: key,
          model_name: modelSelect.value
        })
      });
      const data = await resp.json();
      if (resp.ok && data.success) {
        testKeyStatus.className = 'text-xs font-semibold text-emerald-600';
        testKeyStatus.textContent = '✓ AI 연결 성공!';
      } else {
        testKeyStatus.className = 'text-xs font-semibold text-rose-600';
        testKeyStatus.textContent = `✗ 실패: ${data.detail || '인증 실패'}`;
      }
    } catch (e) {
      testKeyStatus.className = 'text-xs font-semibold text-rose-600';
      testKeyStatus.textContent = `✗ 오류: ${e.message}`;
    }
  });

  // Save Settings
  btnSaveSettings.addEventListener('click', () => {
    const prov = getSelectedModalProvider();
    state.provider = prov;
    localStorage.setItem('esp_provider', prov);

    if (prov === 'gemini') {
      state.geminiKey = apiKeyInput.value.trim();
      state.geminiModel = modelSelect.value;
      localStorage.setItem('esp_gemini_key', state.geminiKey);
      localStorage.setItem('esp_gemini_model', state.geminiModel);
    } else if (prov === 'claude') {
      state.claudeKey = apiKeyInput.value.trim();
      state.claudeModel = modelSelect.value;
      localStorage.setItem('esp_claude_key', state.claudeKey);
      localStorage.setItem('esp_claude_model', state.claudeModel);
    } else if (prov === 'openai') {
      state.openaiKey = apiKeyInput.value.trim();
      state.openaiModel = modelSelect.value;
      localStorage.setItem('esp_openai_key', state.openaiKey);
      localStorage.setItem('esp_openai_model', state.openaiModel);
    }

    updateProviderBadge();
    settingsModal.classList.add('hidden');
    showToast('AI 설정이 저장되었습니다.');
  });

  // Helpers
  function copyPlainText(text, msg) {
    navigator.clipboard.writeText(text).then(() => {
      showToast(msg);
    }).catch(() => {
      showToast('클립보드 복사에 실패했습니다.', true);
    });
  }

  function copyRichText(html, plain, msg) {
    if (navigator.clipboard && window.ClipboardItem) {
      const textBlob = new Blob([plain], { type: 'text/plain' });
      const htmlBlob = new Blob([html], { type: 'text/html' });
      navigator.clipboard.write([
        new ClipboardItem({
          'text/plain': textBlob,
          'text/html': htmlBlob
        })
      ]).then(() => {
        showToast(msg);
      }).catch(err => {
        console.warn('Rich copy fallback to plain text:', err);
        copyPlainText(plain, msg);
      });
    } else {
      copyPlainText(plain, msg);
    }
  }

  function showToast(message, isError = false) {
    toastMessage.textContent = message;
    if (isError) {
      toast.classList.remove('bg-slate-900');
      toast.classList.add('bg-rose-900');
    } else {
      toast.classList.remove('bg-rose-900');
      toast.classList.add('bg-slate-900');
    }
    toast.classList.remove('opacity-0', 'translate-y-10', 'pointer-events-none');
    setTimeout(() => {
      toast.classList.add('opacity-0', 'translate-y-10', 'pointer-events-none');
    }, 3000);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
});
