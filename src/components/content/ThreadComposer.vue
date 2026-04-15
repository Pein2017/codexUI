<template>
  <form
    class="thread-composer"
    :class="{ 'thread-composer--inline-edit': isInlineEdit }"
    @submit.prevent="onSubmit(submitModeForCurrentState)"
  >
    <p v-if="dictationErrorText" class="thread-composer-dictation-error">
      {{ dictationErrorText }}
    </p>

      <div
        class="thread-composer-shell"
        :class="{
          'thread-composer-shell--no-top-radius': hasQueueAbove,
          'thread-composer-shell--drag-active': isDragActive,
          'thread-composer-shell--inline-edit': isInlineEdit,
        }"
      >
      <div v-if="selectedImages.length > 0" class="thread-composer-attachments">
        <div v-for="image in selectedImages" :key="image.id" class="thread-composer-attachment">
          <img class="thread-composer-attachment-image" :src="image.url" :alt="image.name || 'Selected image'" />
          <button
            class="thread-composer-attachment-remove"
            type="button"
            :aria-label="`Remove ${image.name || 'image'}`"
            :disabled="isInteractionDisabled"
            @click="removeImage(image.id)"
          >
            x
          </button>
        </div>
      </div>

      <div v-if="folderUploadGroups.length > 0" class="thread-composer-folder-chips">
        <span v-for="group in folderUploadGroups" :key="group.id" class="thread-composer-folder-chip">
          <IconTablerFolder class="thread-composer-folder-chip-icon" />
          <span class="thread-composer-folder-chip-name" :title="group.name">{{ group.name }}</span>
          <span class="thread-composer-folder-chip-meta">
            <template v-if="group.isUploading">
              {{ getFolderUploadPercent(group) }}% uploading ({{ group.processed }}/{{ group.total }})
            </template>
            <template v-else>
              {{ group.filePaths.length }} file{{ group.filePaths.length === 1 ? '' : 's' }}
            </template>
          </span>
          <button
            class="thread-composer-folder-chip-remove"
            type="button"
            :aria-label="`Remove folder ${group.name}`"
            :disabled="isInteractionDisabled"
            @click="removeFolderAttachment(group.id)"
          >×</button>
        </span>
      </div>

      <div v-if="standaloneFileAttachments.length > 0" class="thread-composer-file-chips">
        <span v-for="att in standaloneFileAttachments" :key="att.fsPath" class="thread-composer-file-chip">
          <IconTablerFolder v-if="att.kind === 'folder'" class="thread-composer-file-chip-icon thread-composer-file-chip-icon--folder" />
          <IconTablerFilePencil v-else class="thread-composer-file-chip-icon" />
          <span class="thread-composer-file-chip-name" :title="att.fsPath">{{ att.label }}</span>
          <button
            class="thread-composer-file-chip-remove"
            type="button"
            :aria-label="`Remove ${att.label}`"
            :disabled="isInteractionDisabled"
            @click="removeFileAttachment(att.fsPath)"
          >×</button>
        </span>
      </div>

      <div v-if="selectedSkills.length > 0" class="thread-composer-skill-chips">
        <span v-for="skill in selectedSkills" :key="skill.path" class="thread-composer-skill-chip">
          <span class="thread-composer-skill-chip-name">{{ skill.name }}</span>
          <button
            class="thread-composer-skill-chip-remove"
            type="button"
            :aria-label="`Remove skill ${skill.name}`"
            @click="removeSkill(skill.path)"
          >×</button>
        </span>
      </div>

      <div
        class="thread-composer-input-wrap"
        :class="{ 'thread-composer-input-wrap--drag-active': isDragActive }"
        @dragenter="onInputDragEnter"
        @dragover="onInputDragOver"
        @dragleave="onInputDragLeave"
        @drop="onInputDrop"
      >
        <div v-if="isDragActive" class="thread-composer-drop-overlay" aria-hidden="true">
          <span class="thread-composer-drop-overlay-copy">Drop images or files</span>
        </div>
        <div v-if="isFileMentionOpen" class="thread-composer-file-mentions">
          <div class="thread-composer-file-mentions-header">
            <span class="thread-composer-file-mentions-title">Mention files or folders</span>
            <span class="thread-composer-file-mentions-hint">{{ fileMentionHintText }}</span>
          </div>
          <template v-if="fileMentionSuggestions.length > 0">
            <button
              v-for="(item, index) in fileMentionSuggestions"
              :key="item.path"
              class="thread-composer-file-mention-row"
              :class="{ 'is-active': index === fileMentionHighlightedIndex }"
              type="button"
              @mousedown.prevent="applyFileMention(item)"
            >
              <span
                v-if="getMentionBadgeText(item.path)"
                class="thread-composer-file-mention-icon-badge"
                :class="`is-${getMentionBadgeClass(item.path)}`"
              >
                {{ getMentionBadgeText(item.path) }}
              </span>
              <IconTablerFolder v-else-if="item.kind === 'folder'" class="thread-composer-file-mention-icon-file" />
              <span v-else-if="isMarkdownFile(item.path)" class="thread-composer-file-mention-icon-markdown">↓</span>
              <IconTablerFilePencil v-else class="thread-composer-file-mention-icon-file" />
              <span class="thread-composer-file-mention-text">
                <span class="thread-composer-file-mention-name">{{ getMentionFileName(item.path) }}</span>
                <span v-if="getMentionDirName(item.path)" class="thread-composer-file-mention-dir">{{ getMentionDirName(item.path) }}</span>
              </span>
            </button>
          </template>
          <div v-else class="thread-composer-file-mention-empty">No matching files</div>
        </div>
        <textarea
          ref="inputRef"
          v-model="draft"
          class="thread-composer-input"
          :class="{ 'thread-composer-input--inline-edit': isInlineEdit }"
          :placeholder="placeholderText"
          :disabled="isInteractionDisabled"
          @input="onInputChange"
          @keydown="onInputKeydown"
          @compositionstart="onInputCompositionStart"
          @compositionend="onInputCompositionEnd"
          @blur="onInputBlur"
          @paste="onInputPaste"
        />
        <ComposerSkillPicker
          :skills="menuOptions"
          :visible="isSlashMenuOpen"
          :anchor-bottom="44"
          :anchor-left="0"
          :search-placeholder="menuSearchPlaceholder"
          @select="onMenuOptionSelect"
          @close="closeSlashMenu"
        />
      </div>

      <div
        class="thread-composer-controls"
        :class="{
          'thread-composer-controls--recording': isDictationRecording,
          'thread-composer-controls--inline-edit': isInlineEdit,
        }"
      >
          <div v-if="!isDictationRecording" class="thread-composer-primary-controls">
          <div v-if="!isInlineEdit" class="thread-composer-runtime-controls">
            <ComposerDropdown
              ref="modelDropdownRef"
              class="thread-composer-control thread-composer-control--model"
              :model-value="selectedModel"
              :options="modelOptions"
              :selected-prefix-icon="showFastModeModelIcon ? IconTablerBolt : null"
              placeholder="Model"
              open-direction="up"
              :disabled="disabled || !activeThreadId || models.length === 0"
              @update:model-value="onModelSelect"
            />

            <ComposerDropdown
              class="thread-composer-control thread-composer-control--reasoning"
              :model-value="selectedReasoningEffort"
              :options="reasoningOptions"
              placeholder="Thinking"
              open-direction="up"
              :disabled="disabled || !activeThreadId"
              @update:model-value="onReasoningEffortSelect"
            />
          </div>

          <div ref="attachMenuRootRef" class="thread-composer-attach">
            <button
              class="thread-composer-attach-trigger"
              type="button"
              aria-label="Add photos & files"
              :disabled="isInteractionDisabled"
              @click="toggleAttachMenu"
            >
              +
            </button>

            <div v-if="isAttachMenuOpen" class="thread-composer-attach-menu">
              <button
                class="thread-composer-attach-item"
                type="button"
                :disabled="isInteractionDisabled"
                @click="triggerPhotoLibrary"
              >
                Add photos & files
              </button>
              <button
                class="thread-composer-attach-item"
                type="button"
                :disabled="isInteractionDisabled"
                @click="triggerFolderPicker"
              >
                Add folder
              </button>
              <button
                class="thread-composer-attach-item"
                type="button"
                :disabled="isInteractionDisabled"
                @click="triggerCameraCapture"
              >
                Take photo
              </button>
              <template v-if="!isInlineEdit">
                <div class="thread-composer-attach-separator" />
                <div class="thread-composer-attach-mode">
                  <span class="thread-composer-attach-mode-label">In-progress send</span>
                  <div class="thread-composer-attach-mode-buttons">
                    <button
                      class="thread-composer-attach-mode-button"
                      :class="{ 'is-active': activeInProgressMode === 'steer' }"
                      type="button"
                      :disabled="isInteractionDisabled"
                      @click="setActiveInProgressMode('steer')"
                    >
                      Steer
                    </button>
                    <button
                      class="thread-composer-attach-mode-button"
                      :class="{ 'is-active': activeInProgressMode === 'queue' }"
                      type="button"
                      :disabled="isInteractionDisabled"
                      @click="setActiveInProgressMode('queue')"
                    >
                      Queue
                    </button>
                  </div>
                </div>
                <div class="thread-composer-attach-separator" />
                <button
                  v-if="isFastModeSupported"
                  class="thread-composer-attach-setting"
                  type="button"
                  role="switch"
                  :aria-checked="selectedSpeedMode === 'fast'"
                  :aria-label="`Fast mode ${selectedSpeedMode === 'fast' ? 'enabled' : 'disabled'}`"
                  :disabled="isSpeedToggleDisabled"
                  @click="onToggleSpeedMode"
                >
                  <span class="thread-composer-attach-setting-copy">
                    <span class="thread-composer-attach-setting-label">Fast mode</span>
                    <span class="thread-composer-attach-setting-description">{{ speedModeDescription }}</span>
                  </span>
                  <span
                    class="thread-composer-attach-switch"
                    :class="{
                      'is-on': selectedSpeedMode === 'fast',
                      'is-busy': isUpdatingSpeedMode,
                      'is-disabled': isSpeedToggleDisabled,
                    }"
                  />
                </button>
                <button
                  class="thread-composer-attach-setting"
                  type="button"
                  role="switch"
                  :aria-checked="isPlanModeSelected"
                  :aria-label="isPlanModeSelected ? 'Disable plan mode' : 'Enable plan mode'"
                  :disabled="disabled || !activeThreadId || isTurnInProgress"
                  @click="toggleCollaborationMode"
                >
                  <span class="thread-composer-attach-setting-copy">
                    <span class="thread-composer-attach-setting-label">Plan mode</span>
                    <span class="thread-composer-attach-setting-description">Agent proposes a plan before acting</span>
                  </span>
                  <span
                    class="thread-composer-attach-switch"
                    :class="{ 'is-on': isPlanModeSelected }"
                  />
                </button>
              </template>
            </div>
          </div>

          <div v-if="!isInlineEdit && (showCompactButton || contextUsageSummaryText)" class="thread-composer-meta-controls">
            <button
              v-if="showCompactButton"
              class="thread-composer-command-button"
              :class="{ 'is-busy': isCompacting }"
              type="button"
              :disabled="disabled || !activeThreadId || isThreadBusyComputed"
              aria-label="Compact thread context"
              :title="compactButtonTitle"
              @click="emit('compact')"
            >
              {{ compactButtonLabel }}
            </button>

            <span
              v-if="isCompacting"
              class="thread-composer-compact-status-badge"
              aria-live="polite"
            >
              Compacting…
            </span>

            <span
              v-if="contextUsageSummaryText"
              class="thread-composer-context-badge"
              :class="{
                'is-warning': contextUsageTone === 'warning',
                'is-danger': contextUsageTone === 'danger',
              }"
              :title="contextUsageTooltipText"
            >
              {{ contextUsageSummaryText }}
            </span>
          </div>
        </div>

        <div
          class="thread-composer-actions"
          :class="{ 'thread-composer-actions--recording': isDictationRecording }"
        >
          <div v-if="dictationState === 'recording'" class="thread-composer-dictation-waveform-wrap" aria-hidden="true">
            <canvas ref="dictationWaveformCanvasRef" class="thread-composer-dictation-waveform" />
          </div>

          <span v-if="dictationState === 'recording'" class="thread-composer-dictation-timer">
            {{ dictationDurationLabel }}
          </span>

          <button
            v-if="isDictationSupported && !isInlineEdit"
            class="thread-composer-mic"
            :class="{
              'thread-composer-mic--active': dictationState === 'recording',
            }"
            type="button"
            :aria-label="dictationButtonLabel"
            :title="dictationButtonLabel"
            :disabled="isInteractionDisabled"
            @click="onDictationToggle"
            @pointerdown="onDictationPressStart"
            @pointerup="onDictationPressEnd"
            @pointercancel="onDictationPressEnd"
          >
            <IconTablerPlayerStopFilled
              v-if="dictationState === 'recording'"
              class="thread-composer-mic-icon thread-composer-mic-icon--stop"
            />
            <IconTablerMicrophone v-else class="thread-composer-mic-icon" />
          </button>

          <button
            v-if="isTurnInProgress && !hasSubmitContent"
            class="thread-composer-stop"
            type="button"
            aria-label="Stop"
            :disabled="disabled || !activeThreadId || isInterruptingTurn"
            @click="onInterrupt"
          >
            <IconTablerPlayerStopFilled class="thread-composer-stop-icon" />
          </button>
          <button
            v-else
            class="thread-composer-submit"
            :class="{ 'thread-composer-submit--queue': submitModeForCurrentState === 'queue' }"
            type="button"
            :aria-label="submitButtonLabel"
            :title="submitButtonTitle"
            :disabled="!canSubmit"
            @click="onSubmit(submitModeForCurrentState)"
          >
            <IconTablerArrowUp class="thread-composer-submit-icon" />
          </button>
        </div>
      </div>

    </div>
    <input
      ref="photoLibraryInputRef"
      class="thread-composer-hidden-input"
      type="file"
      multiple
      :disabled="isInteractionDisabled"
      @change="onPhotoLibraryChange"
    />
    <input
      ref="cameraCaptureInputRef"
      class="thread-composer-hidden-input"
      type="file"
      accept="image/*"
      capture="environment"
      :disabled="isInteractionDisabled"
      @change="onCameraCaptureChange"
    />
    <input
      ref="folderPickerInputRef"
      class="thread-composer-hidden-input"
      type="file"
      multiple
      webkitdirectory
      directory
      :disabled="isInteractionDisabled"
      @change="onFolderPickerChange"
    />
  </form>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type {
  CollaborationModeKind,
  CollaborationModeOption,
  ReasoningEffort,
  SpeedMode,
  UiRateLimitSnapshot,
  UiRateLimitWindow,
  UiThreadTokenUsage,
  UiTokenUsageBreakdown,
} from '../../types/codex'
import { useDictation } from '../../composables/useDictation'
import { useMobile } from '../../composables/useMobile'
import { searchComposerFiles, uploadFile, type ComposerFileSuggestion } from '../../api/codexGateway'
import IconTablerArrowUp from '../icons/IconTablerArrowUp.vue'
import IconTablerBolt from '../icons/IconTablerBolt.vue'
import IconTablerFilePencil from '../icons/IconTablerFilePencil.vue'
import IconTablerFolder from '../icons/IconTablerFolder.vue'
import IconTablerMicrophone from '../icons/IconTablerMicrophone.vue'
import IconTablerPlayerStopFilled from '../icons/IconTablerPlayerStopFilled.vue'
import ComposerDropdown from './ComposerDropdown.vue'
import ComposerSkillPicker from './ComposerSkillPicker.vue'

type SkillItem = { name: string; description: string; path: string }
export type ThreadComposerSlashCommand =
  | 'fork'
  | 'mcp'
  | 'resume'
  | 'review'
  | 'status'

type SlashCommandId =
  | 'collab'
  | 'compact'
  | 'fork'
  | 'mcp'
  | 'model'
  | 'plan'
  | 'resume'
  | 'review'
  | 'status'

type SlashCommandOption = { name: string; description: string; path: SlashCommandId }

const props = defineProps<{
  activeThreadId: string
  cwd?: string
  collaborationModes?: CollaborationModeOption[]
  selectedCollaborationMode: CollaborationModeKind
  models: string[]
  selectedModel: string
  selectedReasoningEffort: ReasoningEffort | ''
  selectedSpeedMode: SpeedMode
  skills?: SkillItem[]
  threadTokenUsage?: UiThreadTokenUsage | null
  codexQuota?: UiRateLimitSnapshot | null
  isTurnInProgress?: boolean
  isThreadBusy?: boolean
  busyPhase?: 'idle' | 'turn' | 'compacting'
  isInterruptingTurn?: boolean
  isUpdatingSpeedMode?: boolean
  disabled?: boolean
  hasQueueAbove?: boolean
  showCompact?: boolean
  appearance?: 'default' | 'inline-edit'
  persistDraft?: boolean
  sendWithEnter?: boolean
  inProgressSubmitMode?: 'steer' | 'queue'
  dictationClickToToggle?: boolean
  dictationAutoSend?: boolean
  dictationLanguage?: string
}>()

export type FileAttachment = { label: string; path: string; fsPath: string; kind?: 'file' | 'folder' }

export type ComposerDraftPayload = {
  text: string
  imageUrls: string[]
  fileAttachments: FileAttachment[]
  skills: Array<{ name: string; path: string }>
}

export type SubmitPayload = {
  text: string
  imageUrls: string[]
  fileAttachments: FileAttachment[]
  skills: Array<{ name: string; path: string }>
  mode: 'steer' | 'queue'
}

export type ThreadComposerExposed = {
  hydrateDraft: (payload: ComposerDraftPayload) => void
  hasUnsavedDraft: () => boolean
  clearDraft: () => void
}

const emit = defineEmits<{
  submit: [payload: SubmitPayload]
  compact: []
  interrupt: []
  'slash-command': [command: ThreadComposerSlashCommand]
  'update:selected-collaboration-mode': [mode: CollaborationModeKind]
  'update:selected-model': [modelId: string]
  'update:selected-reasoning-effort': [effort: ReasoningEffort | '']
  'update:selected-speed-mode': [mode: SpeedMode]
}>()

type SelectedImage = {
  id: string
  name: string
  url: string
}

type FolderUploadGroup = {
  id: string
  name: string
  total: number
  processed: number
  filePaths: string[]
  isUploading: boolean
}

type DropdownExposed = {
  openMenu: () => void
  closeMenu: () => void
}

type AttachmentBatchStats = {
  total: number
  succeeded: number
  failed: number
}

type RecentMentionEntry = {
  path: string
  kind: 'file' | 'folder'
}

type WarmComposerSuggestionCacheEntry = {
  rows: ComposerFileSuggestion[]
  warmedAtMs: number
  pending: Promise<void> | null
}

const CONTEXT_WINDOW_BASELINE_TOKENS = 12000
const DEFAULT_EFFECTIVE_CONTEXT_WINDOW_PERCENT = 95
const DEFAULT_AUTO_COMPACT_PERCENT = 90
const PASTED_TEXT_FILE_THRESHOLD = 2000
const FILE_MENTION_DEBOUNCE_MS = 80
const EMPTY_FILE_MENTION_DEBOUNCE_MS = 0
const WARM_FILE_MENTION_LIMIT = 200
const WARM_FILE_MENTION_CACHE_TTL_MS = 15_000

const draft = ref('')
const selectedImages = ref<SelectedImage[]>([])
const selectedSkills = ref<SkillItem[]>([])
const fileAttachments = ref<FileAttachment[]>([])
const folderUploadGroups = ref<FolderUploadGroup[]>([])

const dictationFeedback = ref('')
const pendingAttachmentCount = ref(0)
const attachmentBatchStats = ref<AttachmentBatchStats | null>(null)
const isDragActive = ref(false)
const {
  state: dictationState,
  isSupported: isDictationSupported,
  recordingDurationMs,
  waveformCanvasRef: dictationWaveformCanvasRef,
  startRecording,
  stopRecording,
  toggleRecording,
  cancel: cancelDictation,
} = useDictation({
  getLanguage: () => props.dictationLanguage ?? 'auto',
  onTranscript: (text) => {
    draft.value = draft.value ? `${draft.value}\n${text}` : text
    dictationFeedback.value = ''
    if (props.dictationAutoSend !== false) {
      onSubmit(submitModeForCurrentState.value)
      return
    }
    nextTick(() => inputRef.value?.focus())
  },
  onEmpty: () => {
    dictationFeedback.value = props.dictationClickToToggle
      ? 'No speech detected. Click again after speaking.'
      : 'No speech detected. Hold the mic and speak.'
  },
  onError: (error) => {
    if (error instanceof DOMException && error.name === 'NotAllowedError') {
      dictationFeedback.value = 'Microphone access was denied.'
      return
    }
    dictationFeedback.value = error instanceof Error ? error.message : 'Dictation failed.'
  },
})
const attachMenuRootRef = ref<HTMLElement | null>(null)
const photoLibraryInputRef = ref<HTMLInputElement | null>(null)
const cameraCaptureInputRef = ref<HTMLInputElement | null>(null)
const folderPickerInputRef = ref<HTMLInputElement | null>(null)
const inputRef = ref<HTMLTextAreaElement | null>(null)
const modelDropdownRef = ref<DropdownExposed | null>(null)
const { isMobile } = useMobile()
const isAttachMenuOpen = ref(false)
const isSlashMenuOpen = ref(false)
const menuMode = ref<'slash' | 'skill' | null>(null)
const isImeComposing = ref(false)
const mentionStartIndex = ref<number | null>(null)
const mentionQuery = ref('')
const fileMentionSuggestions = ref<ComposerFileSuggestion[]>([])
const isFileMentionOpen = ref(false)
const fileMentionHighlightedIndex = ref(0)
const draftGeneration = ref(0)
let fileMentionSearchToken = 0
let fileMentionDebounceTimer: ReturnType<typeof setTimeout> | null = null
let isHoldPressActive = false
let dragDepth = 0
let attachmentSessionToken = 0
const isAndroid = typeof navigator !== 'undefined' && /Android/i.test(navigator.userAgent)
const DRAFT_STORAGE_PREFIX = 'codex-web-local.thread-draft.v1.'
const RECENT_MENTION_STORAGE_PREFIX = 'codex-web-local.composer-recent-mentions.v1.'
let lastActiveThreadId = ''
const warmComposerSuggestionCacheByCwd = new Map<string, WarmComposerSuggestionCacheEntry>()

const reasoningOptions: Array<{ value: ReasoningEffort; label: string }> = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'xhigh', label: 'Extra high' },
]
function formatModelLabel(modelId: string): string {
  return modelId.trim().replace(/^gpt/i, 'GPT')
}

const modelOptions = computed(() =>
  props.models.map((modelId) => ({ value: modelId, label: formatModelLabel(modelId) })),
)
const isPlanModeSelected = computed(() => props.selectedCollaborationMode === 'plan')

const isPlanModeWaitingForModel = computed(() =>
  props.selectedCollaborationMode === 'plan' && props.selectedModel.trim().length === 0,
)

const skillOptions = computed<SkillItem[]>(() => props.skills ?? [])
const slashCommandOptions = computed<SlashCommandOption[]>(() => {
  const options: SlashCommandOption[] = []
  if (showCompactButton.value) {
    options.push({
      name: '/compact',
      description: 'Summarize earlier messages to free context',
      path: 'compact',
    })
  }
  if (hasSelectedThreadContext.value) {
    options.push({
      name: '/review',
      description: 'Review the current thread workspace changes',
      path: 'review',
    })
    options.push({
      name: '/fork',
      description: 'Fork the current chat',
      path: 'fork',
    })
  }
  options.push({
    name: '/resume',
    description: 'Resume a stored session',
    path: 'resume',
  })
  if (canUseGlobalSlashControls.value && props.models.length > 0) {
    options.push({
      name: '/model',
      description: 'Choose what model and reasoning effort to use',
      path: 'model',
    })
  }
  if (canUseGlobalSlashControls.value) {
    options.push({
      name: '/plan',
      description: 'Switch to Plan mode',
      path: 'plan',
    })
    options.push({
      name: '/collab',
      description: 'Change collaboration mode',
      path: 'collab',
    })
  }
  options.push({
    name: '/status',
    description: 'Show current session configuration and token usage',
    path: 'status',
  })
  options.push({
    name: '/mcp',
    description: 'List configured MCP tools',
    path: 'mcp',
  })
  return options
})
const menuOptions = computed(() =>
  menuMode.value === 'slash' ? slashCommandOptions.value : skillOptions.value,
)
const menuSearchPlaceholder = computed(() =>
  menuMode.value === 'slash' ? 'Search commands...' : 'Search skills...',
)

const canSubmit = computed(() => {
  if (props.disabled) return false
  if (props.isUpdatingSpeedMode) return false
  if (!props.activeThreadId) return false
  if (isPlanModeWaitingForModel.value) return false
  if (pendingAttachmentCount.value > 0) return false
  return draft.value.trim().length > 0 || selectedImages.value.length > 0 || fileAttachments.value.length > 0
})
const hasUnsavedDraft = computed(() =>
  draft.value.trim().length > 0
  || selectedImages.value.length > 0
  || selectedSkills.value.length > 0
  || fileAttachments.value.length > 0
  || folderUploadGroups.value.length > 0,
)
const standaloneFileAttachments = computed(() => {
  const grouped = new Set<string>()
  for (const group of folderUploadGroups.value) {
    for (const path of group.filePaths) grouped.add(path)
  }
  return fileAttachments.value.filter((att) => !grouped.has(att.fsPath))
})
const isInteractionDisabled = computed(() => props.disabled || !props.activeThreadId)
const shouldPersistDraft = computed(() => props.persistDraft !== false)
const isInlineEdit = computed(() => props.appearance === 'inline-edit')
const isFastModeSupported = computed(() => props.selectedModel.trim() === 'gpt-5.4')
const showFastModeModelIcon = computed(() =>
  props.selectedSpeedMode === 'fast' && isFastModeSupported.value,
)
const isSpeedToggleDisabled = computed(() =>
  isInteractionDisabled.value || props.isUpdatingSpeedMode === true,
)
const showCompactButton = computed(() => props.showCompact === true)
const isThreadBusyComputed = computed(() => props.isThreadBusy === true || props.isTurnInProgress === true)
const hasSelectedThreadContext = computed(() =>
  showCompactButton.value && props.activeThreadId.trim().length > 0,
)
const isCompacting = computed(() => props.busyPhase === 'compacting')
const canUseGlobalSlashControls = computed(() =>
  !props.disabled && props.activeThreadId.trim().length > 0 && !isInlineEdit.value,
)
const compactButtonLabel = computed(() => isCompacting.value ? 'Compacting…' : 'Compact')
const compactButtonTitle = computed(() =>
  isCompacting.value
    ? 'Compacting is already in progress'
    : isThreadBusyComputed.value
      ? 'Compact is unavailable while this thread is busy'
      : 'Summarize earlier messages to free context',
)
const speedModeDescription = computed(() => {
  if (props.isUpdatingSpeedMode) {
    return 'Applying speed mode for this turn...'
  }
  return props.selectedSpeedMode === 'fast'
    ? 'About 1.5x faster on the next turn, with credits used at 2x'
    : 'Default speed on the next turn with normal credit usage'
})
const inProgressMode = computed<'steer' | 'queue'>(() =>
  props.inProgressSubmitMode === 'steer' ? 'steer' : 'queue',
)
const activeInProgressMode = ref<'steer' | 'queue'>(inProgressMode.value)
const submitModeForCurrentState = computed<'steer' | 'queue'>(() => {
  if (props.busyPhase === 'compacting') return 'queue'
  if (props.isTurnInProgress) return activeInProgressMode.value
  return 'steer'
})
const submitButtonLabel = computed(() =>
  submitModeForCurrentState.value === 'queue' ? 'Queue message' : 'Send message',
)
const submitButtonTitle = computed(() => {
  if (props.busyPhase === 'compacting') {
    return 'Queue message to send right after compaction finishes'
  }
  if (props.isTurnInProgress) {
    return `Send as ${activeInProgressMode.value}`
  }
  return 'Send'
})
const isDictationRecording = computed(() => dictationState.value === 'recording')
const dictationButtonLabel = computed(() => {
  if (dictationState.value === 'recording') return 'Stop dictation'
  return props.dictationClickToToggle ? 'Click to dictate' : 'Hold to dictate'
})
const dictationErrorText = computed(() =>
  dictationState.value === 'idle' ? dictationFeedback.value.trim() : '',
)
const attachmentFeedbackText = computed(() => {
  const stats = attachmentBatchStats.value
  if (stats) {
    const completed = stats.succeeded + stats.failed
    const remaining = Math.max(0, stats.total - completed)
    if (remaining > 0) {
      if (stats.failed > 0) {
        return `${stats.failed} failed, attaching ${formatAttachmentFileCount(remaining)}...`
      }
      return remaining === 1 ? 'Attaching file...' : `Attaching ${remaining} files...`
    }
    if (stats.failed > 0) {
      if (stats.succeeded > 0) {
        return `${stats.succeeded} attached, ${stats.failed} failed.`
      }
      return stats.failed === 1 ? 'Could not attach file.' : `Could not attach ${stats.failed} files.`
    }
  }
  if (pendingAttachmentCount.value <= 0) return ''
  return pendingAttachmentCount.value === 1
    ? 'Attaching file...'
    : `Attaching ${pendingAttachmentCount.value} files...`
})
const dictationDurationLabel = computed(() => {
  const totalSeconds = Math.max(0, Math.floor(recordingDurationMs.value / 1000))
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes}:${String(seconds).padStart(2, '0')}`
})

const placeholderText = computed(() =>
  !props.activeThreadId
    ? 'Select a thread to send a message'
      : isPlanModeWaitingForModel.value
      ? 'Loading models for plan mode...'
      : isMobile.value
        ? 'Message... (@ files, / commands, $ skills)'
        : 'Type a message... (@ for files, / for commands, $ for skills)',
)
const hasSubmitContent = computed(() =>
  draft.value.trim().length > 0 || selectedImages.value.length > 0 || fileAttachments.value.length > 0,
)
const quotaSummaryText = computed(() => buildQuotaSummaryText(props.codexQuota ?? null))
const quotaWeeklyRefreshText = computed(() => '')
const quotaTooltipText = computed(() => buildQuotaTooltipText(props.codexQuota ?? null))
const contextUsageView = computed(() => buildContextUsageView(props.threadTokenUsage ?? null))
const contextUsageSummaryText = computed(() => contextUsageView.value?.summaryText ?? '')
const contextUsageTooltipText = computed(() => contextUsageView.value?.tooltipText ?? '')
const contextUsageTone = computed(() => contextUsageView.value?.tone ?? 'healthy')
const fileMentionHintText = computed(() =>
  mentionQuery.value.trim().length > 0
    ? `Filtering for "${mentionQuery.value.trim()}"`
    : 'Type to filter or pick a recent file or folder from this workspace',
)

function formatPlanType(planType: string | null | undefined): string {
  if (!planType || planType === 'unknown') return ''
  if (planType === 'edu') return 'Education'
  return `${planType.slice(0, 1).toUpperCase()}${planType.slice(1)}`
}

function formatWindowSpan(windowMinutes: number | null): string {
  if (typeof windowMinutes !== 'number' || !Number.isFinite(windowMinutes) || windowMinutes <= 0) return ''
  if (windowMinutes % 1440 === 0) return `${windowMinutes / 1440}d`
  if (windowMinutes % 60 === 0) return `${windowMinutes / 60}h`
  return `${windowMinutes}m`
}

function formatResetTime(resetsAt: number | null): string {
  if (typeof resetsAt !== 'number' || !Number.isFinite(resetsAt)) return ''
  const resetMs = resetsAt * 1000
  const diffMs = resetMs - Date.now()
  if (diffMs <= 0) return 'resetting now'

  const totalMinutes = Math.round(diffMs / 60000)
  if (totalMinutes < 60) return `resets in ${Math.max(1, totalMinutes)}m`

  const totalHours = Math.round(totalMinutes / 60)
  if (totalHours < 48) return `resets in ${Math.max(1, totalHours)}h`

  const totalDays = Math.round(totalHours / 24)
  return `resets in ${Math.max(1, totalDays)}d`
}

function formatResetDate(resetsAt: number | null): string {
  if (typeof resetsAt !== 'number' || !Number.isFinite(resetsAt)) return ''
  return new Intl.DateTimeFormat(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(resetsAt * 1000))
}

function formatResetDateCompact(resetsAt: number | null): string {
  if (typeof resetsAt !== 'number' || !Number.isFinite(resetsAt)) return ''
  const date = new Date(resetsAt * 1000)
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

function pickWeeklyQuotaWindow(quota: UiRateLimitSnapshot): UiRateLimitWindow | null {
  const windows = [quota.primary, quota.secondary].filter((window): window is UiRateLimitWindow => window !== null)
  const exactWeekly = windows.find((window) => window.windowMinutes === 7 * 24 * 60)
  if (exactWeekly) return exactWeekly

  const longerWindows = windows
    .filter((window) => typeof window.windowMinutes === 'number' && window.windowMinutes >= 7 * 24 * 60)
    .sort((first, second) => (first.windowMinutes ?? 0) - (second.windowMinutes ?? 0))

  if (longerWindows[0]) return longerWindows[0]
  return quota.secondary ?? null
}

function formatWindowSummary(window: UiRateLimitWindow): string {
  const remainingPercent = Math.max(0, Math.min(100, 100 - Math.round(window.usedPercent)))
  const span = formatWindowSpan(window.windowMinutes)
  return span ? `${remainingPercent}% / ${span}` : `${remainingPercent}%`
}

function buildQuotaSummaryText(quota: UiRateLimitSnapshot | null): string {
  if (!quota) return ''

  const segments: string[] = []
  const plan = formatPlanType(quota.planType)
  if (plan) segments.push(plan)
  if (quota.primary) segments.push(formatWindowSummary(quota.primary))
  if (quota.secondary) segments.push(formatWindowSummary(quota.secondary))

  const weeklyWindow = pickWeeklyQuotaWindow(quota)
  const weeklyRefreshDate = formatResetDateCompact(weeklyWindow?.resetsAt ?? null)
  if (weeklyRefreshDate) {
    segments.push(weeklyRefreshDate)
  }

  if (segments.length === 0 && quota.credits?.unlimited) {
    segments.push('Unlimited credits')
  } else if (segments.length === 0 && quota.credits?.hasCredits && quota.credits.balance) {
    segments.push(`${quota.credits.balance} credits`)
  }

  return segments.join(' · ')
}

function buildQuotaTooltipText(quota: UiRateLimitSnapshot | null): string {
  if (!quota) return ''

  const lines: string[] = []
  const plan = formatPlanType(quota.planType)
  if (plan) {
    lines.push(`Plan: ${plan}`)
  }

  if (quota.primary) {
    const reset = formatResetTime(quota.primary.resetsAt)
    lines.push(`Primary window: ${formatWindowSummary(quota.primary)}${reset ? `, ${reset}` : ''}`)
  }

  if (quota.secondary) {
    const reset = formatResetTime(quota.secondary.resetsAt)
    lines.push(`Secondary window: ${formatWindowSummary(quota.secondary)}${reset ? `, ${reset}` : ''}`)
  }

  if (quota.credits?.unlimited) {
    lines.push('Credits: unlimited')
  } else if (quota.credits?.hasCredits && quota.credits.balance) {
    lines.push(`Credits: ${quota.credits.balance}`)
  }

  const weeklyWindow = pickWeeklyQuotaWindow(quota)
  if (weeklyWindow) {
    const weeklyRefreshDate = formatResetDate(weeklyWindow.resetsAt)
    if (weeklyRefreshDate) {
      lines.push(`Weekly refresh: ${weeklyRefreshDate}`)
    }
  }

  return lines.join('\n')
}

function buildQuotaWeeklyRefreshText(quota: UiRateLimitSnapshot | null): string {
  if (!quota) return ''
  const weeklyWindow = pickWeeklyQuotaWindow(quota)
  if (!weeklyWindow) return ''
  const weeklyRefreshDate = formatResetDate(weeklyWindow.resetsAt)
  return weeklyRefreshDate ? `Weekly refresh ${weeklyRefreshDate}` : ''
}

function formatCompactTokenCount(value: number): string {
  if (!Number.isFinite(value)) return '0'
  const absValue = Math.abs(value)
  if (absValue >= 1_000_000) {
    const compact = absValue >= 10_000_000 ? (value / 1_000_000).toFixed(0) : (value / 1_000_000).toFixed(1)
    return `${compact.replace(/\.0$/, '')}M`
  }
  if (absValue >= 1_000) {
    const compact = absValue >= 100_000 ? (value / 1_000).toFixed(0) : (value / 1_000).toFixed(1)
    return `${compact.replace(/\.0$/, '')}k`
  }
  return String(Math.round(value))
}

function formatBreakdownSummary(breakdown: UiTokenUsageBreakdown): string {
  const nonCachedInput = Math.max(0, breakdown.inputTokens - breakdown.cachedInputTokens)
  const parts = [
    `${formatCompactTokenCount(breakdown.totalTokens)} total`,
    `${formatCompactTokenCount(nonCachedInput)} input`,
  ]
  if (breakdown.cachedInputTokens > 0) {
    parts.push(`${formatCompactTokenCount(breakdown.cachedInputTokens)} cached`)
  }
  if (breakdown.outputTokens > 0) {
    parts.push(`${formatCompactTokenCount(breakdown.outputTokens)} output`)
  }
  if (breakdown.reasoningOutputTokens > 0) {
    parts.push(`${formatCompactTokenCount(breakdown.reasoningOutputTokens)} reasoning`)
  }
  return parts.join(' · ')
}

function calculateContextPercentRemaining(tokensInContext: number, contextWindow: number): number {
  // Mirror official Codex normalization so the first prompt does not look artificially "used".
  if (!Number.isFinite(tokensInContext) || !Number.isFinite(contextWindow) || contextWindow <= 0) {
    return 0
  }
  if (contextWindow <= CONTEXT_WINDOW_BASELINE_TOKENS) {
    const remaining = Math.max(0, contextWindow - Math.max(0, tokensInContext))
    return Math.max(0, Math.min(100, Math.round((remaining / contextWindow) * 100)))
  }
  const effectiveWindow = contextWindow - CONTEXT_WINDOW_BASELINE_TOKENS
  const used = Math.max(0, tokensInContext - CONTEXT_WINDOW_BASELINE_TOKENS)
  const remaining = Math.max(0, effectiveWindow - used)
  return Math.max(0, Math.min(100, Math.round((remaining / effectiveWindow) * 100)))
}

function inferAutoCompactTokenLimit(contextWindow: number): number {
  if (!Number.isFinite(contextWindow) || contextWindow <= 0) {
    return 0
  }
  const inferred = Math.round((contextWindow * DEFAULT_AUTO_COMPACT_PERCENT) / DEFAULT_EFFECTIVE_CONTEXT_WINDOW_PERCENT)
  return Math.max(1, Math.min(contextWindow, inferred))
}

function buildContextUsageView(
  usage: UiThreadTokenUsage | null,
): {
    summaryText: string
    tooltipText: string
    tone: 'healthy' | 'warning' | 'danger'
  } | null {
  if (!usage) return null

  const contextWindow = usage.modelContextWindow ?? null
  if (typeof contextWindow !== 'number' || !Number.isFinite(contextWindow) || contextWindow <= 0) return null

  const tokensInContext = Math.max(0, usage.last.totalTokens)
  const autoCompactLimit = inferAutoCompactTokenLimit(contextWindow)
  const percentRemaining = calculateContextPercentRemaining(tokensInContext, autoCompactLimit)
  const percentUsed = Math.max(0, Math.min(100, 100 - percentRemaining))
  const tone: 'healthy' | 'warning' | 'danger' = percentRemaining <= 15
    ? 'danger'
    : percentRemaining <= 35
      ? 'warning'
      : 'healthy'

  return {
    summaryText: `${percentRemaining}%`,
    tooltipText: [
      `Before auto-compact: ${percentRemaining}% left (${percentUsed}% used)`,
      `Current context: ${tokensInContext.toLocaleString()} / ${autoCompactLimit.toLocaleString()} tokens`,
      `Model context window event: ${contextWindow.toLocaleString()} tokens`,
      'Auto-compact trigger is inferred from Codex defaults when an explicit threshold is unavailable.',
      `Last turn: ${formatBreakdownSummary(usage.last)}`,
      `Session total: ${formatBreakdownSummary(usage.total)}`,
    ].join('\n'),
    tone,
  }
}

function onSubmit(mode: 'steer' | 'queue' = 'steer'): void {
  if (tryExecuteSlashCommand()) {
    return
  }
  const text = draft.value.trim()
  if (!canSubmit.value) return
  emit('submit', {
    text,
    imageUrls: selectedImages.value.map((image) => image.url),
    fileAttachments: [...fileAttachments.value],
    skills: selectedSkills.value.map((s) => ({ name: s.name, path: s.path })),
    mode,
  })
  if (shouldPersistDraft.value) {
    clearPersistedDraftForThread(props.activeThreadId)
  }
  clearDraftState()
  folderUploadGroups.value = []
  isAttachMenuOpen.value = false
  isSlashMenuOpen.value = false
  closeFileMention()
  if (isAndroid || isMobile.value) {
    inputRef.value?.blur()
    return
  }
  nextTick(() => inputRef.value?.focus())
}

function setActiveInProgressMode(mode: 'steer' | 'queue'): void {
  activeInProgressMode.value = mode
}

function replaceDraftState(payload: ComposerDraftPayload): void {
  draftGeneration.value += 1
  draft.value = payload.text
  selectedImages.value = payload.imageUrls.map((url, index) => ({
    id: `queued-${Date.now()}-${index}-${Math.random().toString(36).slice(2, 8)}`,
    name: `Image ${index + 1}`,
    url,
  }))
  selectedSkills.value = payload.skills.map((skill) => (
    (props.skills ?? []).find((item) => item.path === skill.path)
    ?? { name: skill.name, description: '', path: skill.path }
  ))
  fileAttachments.value = payload.fileAttachments.map((attachment) => ({ ...attachment }))
  folderUploadGroups.value = []
  dictationFeedback.value = ''
  attachmentBatchStats.value = null
  pendingAttachmentCount.value = 0
  isAttachMenuOpen.value = false
  isSlashMenuOpen.value = false
  closeFileMention()
  attachmentSessionToken += 1
}

function clearDraftState(): void {
  replaceDraftState({
    text: '',
    imageUrls: [],
    fileAttachments: [],
    skills: [],
  })
}

function getDraftStorageKey(threadId: string): string {
  return `${DRAFT_STORAGE_PREFIX}${threadId}`
}

function getRecentMentionStorageKey(cwd: string): string {
  return `${RECENT_MENTION_STORAGE_PREFIX}${cwd.trim().replace(/\\/g, '/')}`
}

function normalizeComposerPath(path: string): string {
  return path.trim().replace(/\\/g, '/')
}

function loadPersistedDraftForThread(threadId: string): ComposerDraftPayload | null {
  if (typeof window === 'undefined') return null
  const normalizedThreadId = threadId.trim()
  if (!normalizedThreadId) return null
  try {
    const raw = window.localStorage.getItem(getDraftStorageKey(normalizedThreadId))
    if (!raw) return null
    const parsed = JSON.parse(raw) as Partial<ComposerDraftPayload> | string
    if (typeof parsed === 'string') {
      return {
        text: parsed,
        imageUrls: [],
        fileAttachments: [],
        skills: [],
      }
    }
    return {
      text: typeof parsed.text === 'string' ? parsed.text : '',
      imageUrls: Array.isArray(parsed.imageUrls)
        ? parsed.imageUrls.filter((url): url is string => typeof url === 'string')
        : [],
      fileAttachments: Array.isArray(parsed.fileAttachments)
        ? parsed.fileAttachments.filter((attachment): attachment is FileAttachment => (
          Boolean(attachment)
          && typeof attachment.label === 'string'
          && typeof attachment.path === 'string'
          && typeof attachment.fsPath === 'string'
          && (attachment.kind === undefined || attachment.kind === 'file' || attachment.kind === 'folder')
        ))
        : [],
      skills: Array.isArray(parsed.skills)
        ? parsed.skills.filter((skill): skill is { name: string; path: string } => (
          Boolean(skill)
          && typeof skill.name === 'string'
          && typeof skill.path === 'string'
        ))
        : [],
    }
  } catch {
    return null
  }
}

function persistDraftForThread(threadId: string, payload: ComposerDraftPayload): void {
  if (typeof window === 'undefined') return
  const normalizedThreadId = threadId.trim()
  if (!normalizedThreadId) return
  try {
    const hasContent = payload.text.trim().length > 0
      || payload.imageUrls.length > 0
      || payload.fileAttachments.length > 0
      || payload.skills.length > 0
    if (hasContent) {
      window.localStorage.setItem(getDraftStorageKey(normalizedThreadId), JSON.stringify(payload))
      return
    }
    window.localStorage.removeItem(getDraftStorageKey(normalizedThreadId))
  } catch {
    // Ignore localStorage failures (quota/private mode).
  }
}

function clearPersistedDraftForThread(threadId: string): void {
  persistDraftForThread(threadId, {
    text: '',
    imageUrls: [],
    fileAttachments: [],
    skills: [],
  })
}

function loadRecentMentionEntries(cwd: string): RecentMentionEntry[] {
  if (typeof window === 'undefined') return []
  const normalizedCwd = normalizeComposerPath(cwd)
  if (!normalizedCwd) return []
  try {
    const raw = window.localStorage.getItem(getRecentMentionStorageKey(normalizedCwd))
    if (!raw) return []
    const parsed = JSON.parse(raw) as unknown
    if (!Array.isArray(parsed)) return []
    const entries: RecentMentionEntry[] = []
    for (const value of parsed) {
      if (typeof value === 'string') {
        const normalizedPath = normalizeComposerPath(value)
        if (!normalizedPath) continue
        entries.push({
          path: normalizedPath,
          kind: normalizedPath.endsWith('/') ? 'folder' : 'file',
        })
        continue
      }
      if (!value || typeof value !== 'object' || Array.isArray(value)) continue
      const record = value as Record<string, unknown>
      const normalizedPath = normalizeComposerPath(typeof record.path === 'string' ? record.path : '')
      if (!normalizedPath) continue
      entries.push({
        path: normalizedPath,
        kind: record.kind === 'folder' ? 'folder' : 'file',
      })
    }
    return entries
      .filter((entry, index, rows) => rows.findIndex((candidate) => candidate.path === entry.path) === index)
      .slice(0, 25)
  } catch {
    return []
  }
}

function loadRecentMentionPaths(cwd: string): string[] {
  return loadRecentMentionEntries(cwd).map((entry) => entry.path)
}

function rememberRecentMentionEntry(entry: RecentMentionEntry): void {
  if (typeof window === 'undefined') return
  const normalizedCwd = normalizeComposerPath(props.cwd ?? '')
  const normalizedPath = normalizeComposerPath(entry.path)
  if (!normalizedCwd || !normalizedPath) return
  const nextEntries = [
    { path: normalizedPath, kind: entry.kind },
    ...loadRecentMentionEntries(normalizedCwd).filter((value) => value.path !== normalizedPath),
  ].slice(0, 25)
  try {
    window.localStorage.setItem(getRecentMentionStorageKey(normalizedCwd), JSON.stringify(nextEntries))
  } catch {
    // Ignore localStorage failures.
  }
}

function scoreImmediateMentionCandidate(path: string, query: string): number {
  if (!query) return 0
  const lowerPath = path.toLowerCase()
  const lowerQuery = query.toLowerCase()
  const baseName = lowerPath.slice(lowerPath.lastIndexOf('/') + 1)
  if (baseName === lowerQuery) return 0
  if (baseName.startsWith(lowerQuery)) return 1
  if (baseName.includes(lowerQuery)) return 2
  if (lowerPath.includes(`/${lowerQuery}`)) return 3
  if (lowerPath.includes(lowerQuery)) return 4
  return 10
}

function getWarmComposerSuggestionCacheEntry(cwd: string): WarmComposerSuggestionCacheEntry | null {
  const normalizedCwd = normalizeComposerPath(cwd)
  if (!normalizedCwd) return null
  return warmComposerSuggestionCacheByCwd.get(normalizedCwd) ?? null
}

function setWarmComposerSuggestionCacheEntry(cwd: string, entry: WarmComposerSuggestionCacheEntry): void {
  const normalizedCwd = normalizeComposerPath(cwd)
  if (!normalizedCwd) return
  warmComposerSuggestionCacheByCwd.set(normalizedCwd, entry)
}

function getImmediateFileMentionSuggestions(cwd: string, query: string): ComposerFileSuggestion[] {
  const normalizedQuery = query.trim()
  const recentEntries = loadRecentMentionEntries(cwd).map((entry) => ({
    path: entry.path,
    kind: entry.kind,
  }))
  const warmRows = getWarmComposerSuggestionCacheEntry(cwd)?.rows ?? []
  const merged = [...recentEntries, ...warmRows]
  const deduped = merged.filter((entry, index, rows) => (
    rows.findIndex((candidate) => candidate.path === entry.path) === index
  ))
  return deduped
    .map((entry, index) => ({
      entry,
      score: scoreImmediateMentionCandidate(entry.path, normalizedQuery),
      recentRank: recentEntries.findIndex((candidate) => candidate.path === entry.path),
      originalRank: index,
    }))
    .filter((row) => normalizedQuery.length === 0 || row.score < 10)
    .sort((left, right) =>
      (left.score - right.score)
      || ((left.recentRank < 0 ? Number.POSITIVE_INFINITY : left.recentRank)
        - (right.recentRank < 0 ? Number.POSITIVE_INFINITY : right.recentRank))
      || (left.originalRank - right.originalRank),
    )
    .slice(0, 20)
    .map((row) => row.entry)
}

async function prewarmFileMentionSuggestions(cwd: string): Promise<void> {
  const normalizedCwd = normalizeComposerPath(cwd)
  if (!normalizedCwd) return
  const existing = getWarmComposerSuggestionCacheEntry(normalizedCwd)
  if (existing?.pending) {
    await existing.pending
    return
  }
  const now = Date.now()
  if (existing && (now - existing.warmedAtMs) <= WARM_FILE_MENTION_CACHE_TTL_MS) {
    return
  }
  const pending = (async () => {
    try {
      const rows = await searchComposerFiles(
        normalizedCwd,
        '',
        WARM_FILE_MENTION_LIMIT,
        loadRecentMentionPaths(normalizedCwd),
      )
      setWarmComposerSuggestionCacheEntry(normalizedCwd, {
        rows,
        warmedAtMs: Date.now(),
        pending: null,
      })
    } catch {
      setWarmComposerSuggestionCacheEntry(normalizedCwd, {
        rows: existing?.rows ?? [],
        warmedAtMs: existing?.warmedAtMs ?? 0,
        pending: null,
      })
    }
  })()
  setWarmComposerSuggestionCacheEntry(normalizedCwd, {
    rows: existing?.rows ?? [],
    warmedAtMs: existing?.warmedAtMs ?? 0,
    pending,
  })
  await pending
}

function getCurrentDraftPayload(): ComposerDraftPayload {
  return {
    text: draft.value,
    imageUrls: selectedImages.value.map((image) => image.url),
    fileAttachments: fileAttachments.value.map((attachment) => ({ ...attachment })),
    skills: selectedSkills.value.map((skill) => ({ name: skill.name, path: skill.path })),
  }
}

function onInterrupt(): void {
  emit('interrupt')
}

function onModelSelect(value: string): void {
  emit('update:selected-model', value)
}

function toggleCollaborationMode(): void {
  emit('update:selected-collaboration-mode', isPlanModeSelected.value ? 'default' : 'plan')
}

function openModelPicker(): void {
  modelDropdownRef.value?.openMenu()
}

function openCollaborationMenu(): void {
  if (isInteractionDisabled.value) return
  isAttachMenuOpen.value = true
}

function onReasoningEffortSelect(value: string): void {
  emit('update:selected-reasoning-effort', value as ReasoningEffort)
}

function onToggleSpeedMode(): void {
  if (isSpeedToggleDisabled.value) return
  emit('update:selected-speed-mode', props.selectedSpeedMode === 'fast' ? 'standard' : 'fast')
}

function onDictationToggle(): void {
  if (!props.dictationClickToToggle) return
  if (dictationFeedback.value) {
    dictationFeedback.value = ''
  }
  toggleRecording()
}

function onDictationPressStart(event: PointerEvent): void {
  if (props.dictationClickToToggle) return
  event.preventDefault()
  if (isHoldPressActive) return
  isHoldPressActive = true
  const target = event.currentTarget as HTMLElement | null
  if (target) {
    try {
      target.setPointerCapture(event.pointerId)
    } catch {
      // Ignore if pointer cannot be captured in the current environment.
    }
  }
  if (dictationFeedback.value) {
    dictationFeedback.value = ''
  }
  window.addEventListener('pointerup', onDictationPressEnd)
  window.addEventListener('pointercancel', onDictationPressEnd)
  window.addEventListener('blur', onDictationPressEnd)
  void startRecording()
}

function onDictationPressEnd(): void {
  if (props.dictationClickToToggle) return
  if (!isHoldPressActive) return
  isHoldPressActive = false
  window.removeEventListener('pointerup', onDictationPressEnd)
  window.removeEventListener('pointercancel', onDictationPressEnd)
  window.removeEventListener('blur', onDictationPressEnd)
  stopRecording()
}

function toggleAttachMenu(): void {
  if (isInteractionDisabled.value) return
  isAttachMenuOpen.value = !isAttachMenuOpen.value
}

function triggerPhotoLibrary(): void {
  photoLibraryInputRef.value?.click()
}

function triggerCameraCapture(): void {
  cameraCaptureInputRef.value?.click()
}

function triggerFolderPicker(): void {
  folderPickerInputRef.value?.click()
}

function removeImage(id: string): void {
  selectedImages.value = selectedImages.value.filter((image) => image.id !== id)
}

function removeSkill(path: string): void {
  selectedSkills.value = selectedSkills.value.filter((s) => s.path !== path)
}

function removeFileAttachment(fsPath: string): void {
  fileAttachments.value = fileAttachments.value.filter((a) => a.fsPath !== fsPath)
}

function removeFolderAttachment(groupId: string): void {
  const group = folderUploadGroups.value.find((item) => item.id === groupId)
  if (!group) return
  const toRemove = new Set(group.filePaths)
  fileAttachments.value = fileAttachments.value.filter((a) => !toRemove.has(a.fsPath))
  folderUploadGroups.value = folderUploadGroups.value.filter((item) => item.id !== groupId)
}

function getFolderUploadPercent(group: FolderUploadGroup): number {
  if (group.total <= 0) return 0
  return Math.round((group.processed / group.total) * 100)
}

function buildAttachmentLabel(filePath: string, kind: 'file' | 'folder', customLabel?: string): string {
  const normalized = filePath.replace(/\\/g, '/')
  const parts = normalized.split('/').filter(Boolean)
  const fallbackLabel = parts[parts.length - 1] || normalized
  const baseLabel = customLabel?.trim() || fallbackLabel
  if (kind === 'folder' && !baseLabel.endsWith('/')) {
    return `${baseLabel}/`
  }
  return baseLabel
}

function addFileAttachment(filePath: string, customLabel?: string, kind: 'file' | 'folder' = 'file'): void {
  const normalized = filePath.replace(/\\/g, '/')
  if (fileAttachments.value.some((a) => a.fsPath === normalized)) return
  const label = buildAttachmentLabel(normalized, kind, customLabel)
  fileAttachments.value = [...fileAttachments.value, { label, path: normalized, fsPath: normalized, kind }]
}

function isImageFile(file: File): boolean {
  if (file.type.startsWith('image/')) return true
  return /\.(png|jpe?g|gif|webp)$/i.test(file.name)
}

function normalizeSelectedFiles(files: FileList | File[] | null | undefined): File[] {
  if (!files) return []
  return Array.from(files)
}

function formatAttachmentFileCount(count: number): string {
  return count === 1 ? '1 file' : `${count} files`
}

function beginAttachmentWork(sessionToken: number): boolean {
  if (sessionToken !== attachmentSessionToken) return false
  pendingAttachmentCount.value += 1
  return true
}

function finishAttachmentWork(sessionToken: number): void {
  if (sessionToken !== attachmentSessionToken) return
  pendingAttachmentCount.value = Math.max(0, pendingAttachmentCount.value - 1)
}

function beginAttachmentBatch(total: number): void {
  if (total <= 0) return
  const current = attachmentBatchStats.value
  const completed = current ? current.succeeded + current.failed : 0
  if (!current || completed >= current.total) {
    attachmentBatchStats.value = { total, succeeded: 0, failed: 0 }
    return
  }
  attachmentBatchStats.value = {
    ...current,
    total: current.total + total,
  }
}

function recordAttachmentBatchResult(result: 'success' | 'failure'): void {
  const current = attachmentBatchStats.value
  if (!current) return
  attachmentBatchStats.value = {
    ...current,
    succeeded: current.succeeded + (result === 'success' ? 1 : 0),
    failed: current.failed + (result === 'failure' ? 1 : 0),
  }
}

function createAttachmentId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

function createPastedImageName(file: File): string {
  const now = new Date()
  const timestamp = [
    now.getFullYear(),
    String(now.getMonth() + 1).padStart(2, '0'),
    String(now.getDate()).padStart(2, '0'),
    String(now.getHours()).padStart(2, '0'),
    String(now.getMinutes()).padStart(2, '0'),
    String(now.getSeconds()).padStart(2, '0'),
  ].join('-')
  const ext = file.type.startsWith('image/')
    ? file.type.slice('image/'.length).replace(/[^a-z0-9]+/gi, '') || 'png'
    : 'png'
  return `pasted-image-${timestamp}.${ext}`
}

function createPastedTextFileName(): string {
  const now = new Date()
  const timestamp = [
    now.getFullYear(),
    String(now.getMonth() + 1).padStart(2, '0'),
    String(now.getDate()).padStart(2, '0'),
    String(now.getHours()).padStart(2, '0'),
    String(now.getMinutes()).padStart(2, '0'),
    String(now.getSeconds()).padStart(2, '0'),
  ].join('-')
  return `pasted-text-${timestamp}.txt`
}

function ensureFileName(file: File): File {
  if (file.name.trim()) return file
  return new File([file], createPastedImageName(file), {
    type: file.type || 'image/png',
    lastModified: Date.now(),
  })
}

function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        resolve(reader.result)
        return
      }
      reject(new Error('Image read returned an unsupported result'))
    }
    reader.onerror = () => {
      reject(reader.error ?? new Error('Image read failed'))
    }
    reader.readAsDataURL(file)
  })
}

async function attachImageFile(file: File, sessionToken: number): Promise<void> {
  if (!beginAttachmentWork(sessionToken)) return
  try {
    const normalizedFile = ensureFileName(file)
    const dataUrl = await readFileAsDataUrl(normalizedFile)
    if (sessionToken !== attachmentSessionToken) return
    selectedImages.value = [
      ...selectedImages.value,
      {
        id: createAttachmentId(),
        name: normalizedFile.name,
        url: dataUrl,
      },
    ]
    recordAttachmentBatchResult('success')
  } catch {
    if (sessionToken === attachmentSessionToken) {
      recordAttachmentBatchResult('failure')
    }
  } finally {
    finishAttachmentWork(sessionToken)
  }
}

async function attachUploadedFile(file: File, sessionToken: number): Promise<void> {
  if (!beginAttachmentWork(sessionToken)) return
  try {
    const serverPath = await uploadFile(file)
    if (sessionToken !== attachmentSessionToken) return
    if (!serverPath) {
      recordAttachmentBatchResult('failure')
      return
    }
    addFileAttachment(serverPath)
    recordAttachmentBatchResult('success')
  } catch {
    if (sessionToken === attachmentSessionToken) {
      recordAttachmentBatchResult('failure')
    }
  } finally {
    finishAttachmentWork(sessionToken)
  }
}

function attachIncomingFiles(files: FileList | File[] | null | undefined): void {
  const normalizedFiles = normalizeSelectedFiles(files)
  if (normalizedFiles.length === 0) return
  beginAttachmentBatch(normalizedFiles.length)
  isAttachMenuOpen.value = false
  isSlashMenuOpen.value = false
  closeFileMention()
  const sessionToken = attachmentSessionToken
  for (const file of normalizedFiles) {
    if (isImageFile(file)) {
      void attachImageFile(file, sessionToken)
    } else {
      void attachUploadedFile(file, sessionToken)
    }
  }
}

function resetDragState(): void {
  dragDepth = 0
  isDragActive.value = false
}

function addFiles(files: FileList | null): void {
  if (!files || files.length === 0) return
  const generation = draftGeneration.value
  for (const file of Array.from(files)) {
    if (isImageFile(file)) {
      const reader = new FileReader()
      reader.onload = () => {
        if (generation !== draftGeneration.value) return
        if (typeof reader.result !== 'string') return
        selectedImages.value.push({
          id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
          name: file.name,
          url: reader.result,
        })
      }
      reader.readAsDataURL(file)
    } else {
      void uploadFile(file).then((serverPath) => {
        if (generation !== draftGeneration.value) return
        if (serverPath) addFileAttachment(serverPath)
      }).catch(() => {})
    }
  }
}

function hasFilePayload(dataTransfer: DataTransfer | null): boolean {
  if (!dataTransfer) return false
  return Array.from(dataTransfer.types ?? []).includes('Files')
}

async function addFolderFiles(files: FileList | null): Promise<void> {
  if (!files || files.length === 0) return
  const generation = draftGeneration.value
  const rows = Array.from(files)
  const firstRelativePath = (rows[0] as File & { webkitRelativePath?: string }).webkitRelativePath || rows[0].name
  const folderName = firstRelativePath.split('/').filter(Boolean)[0] || 'Folder'
  const groupId = `${Date.now()}-${Math.random().toString(36).slice(2)}`
  folderUploadGroups.value = [
    ...folderUploadGroups.value,
    {
      id: groupId,
      name: folderName,
      total: rows.length,
      processed: 0,
      filePaths: [],
      isUploading: true,
    },
  ]

  const updateGroup = (updater: (group: FolderUploadGroup) => FolderUploadGroup): void => {
    if (generation !== draftGeneration.value) return
    folderUploadGroups.value = folderUploadGroups.value.map((group) => (
      group.id === groupId ? updater(group) : group
    ))
  }

  for (const file of rows) {
    try {
      const serverPath = await uploadFile(file)
      if (generation !== draftGeneration.value) return
      if (serverPath) {
        const relativePath = (file as File & { webkitRelativePath?: string }).webkitRelativePath || file.name
        addFileAttachment(serverPath, relativePath)
        updateGroup((group) => ({
          ...group,
          processed: group.processed + 1,
          filePaths: [...group.filePaths, serverPath],
        }))
        continue
      }
      updateGroup((group) => ({ ...group, processed: group.processed + 1 }))
    } catch {
      updateGroup((group) => ({ ...group, processed: group.processed + 1 }))
    }
  }

  updateGroup((group) => ({ ...group, isUploading: false }))
}

function clearInputValue(inputRefEl: HTMLInputElement | null): void {
  if (inputRefEl) inputRefEl.value = ''
}

function onPhotoLibraryChange(event: Event): void {
  const input = event.target as HTMLInputElement | null
  addFiles(input?.files ?? null)
  clearInputValue(input)
  isAttachMenuOpen.value = false
}

function onCameraCaptureChange(event: Event): void {
  const input = event.target as HTMLInputElement | null
  addFiles(input?.files ?? null)
  clearInputValue(input)
  isAttachMenuOpen.value = false
}

function onFolderPickerChange(event: Event): void {
  const input = event.target as HTMLInputElement | null
  void addFolderFiles(input?.files ?? null)
  clearInputValue(input)
  isAttachMenuOpen.value = false
}

function onInputDragEnter(event: DragEvent): void {
  if (isInteractionDisabled.value || !hasFilePayload(event.dataTransfer)) return
  event.preventDefault()
  dragDepth += 1
  isDragActive.value = true
}

function onInputDragOver(event: DragEvent): void {
  if (isInteractionDisabled.value || !hasFilePayload(event.dataTransfer)) return
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'copy'
  }
  isDragActive.value = true
}

function onInputDragLeave(event: DragEvent): void {
  if (!isDragActive.value) return
  event.preventDefault()
  dragDepth = Math.max(0, dragDepth - 1)
  if (dragDepth === 0) {
    resetDragState()
  }
}

function onInputDrop(event: DragEvent): void {
  if (isInteractionDisabled.value || !hasFilePayload(event.dataTransfer)) return
  event.preventDefault()
  resetDragState()
  attachIncomingFiles(event.dataTransfer?.files ?? null)
}

function onWindowDragCleanup(): void {
  if (!isDragActive.value && dragDepth === 0) return
  resetDragState()
}

function onInputPaste(event: ClipboardEvent): void {
  if (isInteractionDisabled.value) return
  const plainText = event.clipboardData?.getData('text/plain') ?? ''
  if (plainText.length >= PASTED_TEXT_FILE_THRESHOLD) {
    event.preventDefault()
    const textFile = new File([plainText], createPastedTextFileName(), {
      type: 'text/plain',
      lastModified: Date.now(),
    })
    attachIncomingFiles([textFile])
    return
  }
  const items = Array.from(event.clipboardData?.items ?? [])
  if (items.length === 0) return
  const hasPlainText = plainText.length > 0
  const imageFiles = items
    .filter((item) => item.kind === 'file' && item.type.startsWith('image/'))
    .map((item) => item.getAsFile())
    .filter((file): file is File => file instanceof File)
  if (imageFiles.length === 0) return
  if (!hasPlainText) {
    event.preventDefault()
  }
  attachIncomingFiles(imageFiles)
}

function onInputChange(): void {
  if (dictationFeedback.value) {
    dictationFeedback.value = ''
  }
  const text = draft.value
  const nextMenuMode = text.startsWith('$')
    ? 'skill'
    : text.startsWith('/')
      ? 'slash'
      : null
  if (nextMenuMode !== menuMode.value) {
    menuMode.value = nextMenuMode
  }
  const shouldShowSlashMenu = nextMenuMode !== null
  if (shouldShowSlashMenu !== isSlashMenuOpen.value) {
    isSlashMenuOpen.value = shouldShowSlashMenu
  }
  updateFileMentionState()
}

function onInputCompositionStart(): void {
  isImeComposing.value = true
}

function onInputCompositionEnd(): void {
  isImeComposing.value = false
}

function onInputBlur(): void {
  isImeComposing.value = false
}

function getFileMentionMatch(text: string, cursor: number): { startIndex: number; query: string } | null {
  const beforeCursor = text.slice(0, cursor)
  const match = beforeCursor.match(/(^|\s)(@[^\s@]*)$/)
  if (!match) return null
  const mentionToken = match[2] ?? ''
  return {
    startIndex: cursor - mentionToken.length,
    query: mentionToken.slice(1),
  }
}

function isImeConfirmEnter(event: KeyboardEvent): boolean {
  if (event.key !== 'Enter') {
    return false
  }
  return event.isComposing || isImeComposing.value || event.keyCode === 229
}

function resolveKeyboardSubmitMode(event: KeyboardEvent): 'steer' | 'queue' | null {
  const shouldSteer = props.sendWithEnter !== false
    ? event.key === 'Enter' && !event.shiftKey && !event.metaKey && !event.ctrlKey && !event.altKey
    : event.key === 'Enter' && (event.metaKey || event.ctrlKey)
  if (shouldSteer) {
    return props.busyPhase === 'compacting' ? 'queue' : 'steer'
  }
  const shouldQueue =
    props.sendWithEnter !== false
    && (props.isTurnInProgress === true || props.busyPhase === 'compacting')
    && event.key === 'Tab'
    && !event.shiftKey
    && !event.metaKey
    && !event.ctrlKey
    && !event.altKey
  if (shouldQueue) {
    return 'queue'
  }
  return null
}

function onInputKeydown(event: KeyboardEvent): void {
  if (isImeConfirmEnter(event)) {
    return
  }

  if (isFileMentionOpen.value) {
    if (event.key === 'Escape') {
      event.preventDefault()
      closeFileMention()
      return
    }
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      if (fileMentionSuggestions.value.length > 0) {
        fileMentionHighlightedIndex.value =
          (fileMentionHighlightedIndex.value + 1) % fileMentionSuggestions.value.length
      }
      return
    }
    if (event.key === 'ArrowUp') {
      event.preventDefault()
      if (fileMentionSuggestions.value.length > 0) {
        const size = fileMentionSuggestions.value.length
        fileMentionHighlightedIndex.value = (fileMentionHighlightedIndex.value + size - 1) % size
      }
      return
    }
    if (event.key === 'Enter' || event.key === 'Tab') {
      event.preventDefault()
      const selected = fileMentionSuggestions.value[fileMentionHighlightedIndex.value]
      if (selected) {
        applyFileMention(selected)
      } else {
        closeFileMention()
      }
      return
    }
  }

  const submitMode = resolveKeyboardSubmitMode(event)
  if (submitMode !== null && canSubmit.value) {
    event.preventDefault()
    onSubmit(submitMode)
    return
  }

  if (isSlashMenuOpen.value) {
    if (event.key === 'Escape') {
      event.preventDefault()
      closeSlashMenu()
      return
    }
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault()
      return
    }
  }
}

function closeSlashMenu(): void {
  isSlashMenuOpen.value = false
  menuMode.value = null
  inputRef.value?.focus()
}

function closeFileMention(): void {
  isFileMentionOpen.value = false
  mentionStartIndex.value = null
  mentionQuery.value = ''
  fileMentionSuggestions.value = []
  fileMentionHighlightedIndex.value = 0
}

function updateFileMentionState(): void {
  const input = inputRef.value
  if (!input) {
    closeFileMention()
    return
  }
  const cursor = input.selectionStart ?? draft.value.length
  const mentionMatch = getFileMentionMatch(draft.value, cursor)
  if (!mentionMatch) {
    closeFileMention()
    return
  }
  mentionStartIndex.value = mentionMatch.startIndex
  mentionQuery.value = mentionMatch.query
  isFileMentionOpen.value = true
  const cwd = normalizeComposerPath(props.cwd ?? '')
  if (cwd) {
    const immediateRows = getImmediateFileMentionSuggestions(cwd, mentionQuery.value)
    if (immediateRows.length > 0 || mentionQuery.value.trim().length === 0) {
      fileMentionSuggestions.value = immediateRows
      fileMentionHighlightedIndex.value = 0
    }
    void prewarmFileMentionSuggestions(cwd)
  }
  void queueFileMentionSearch()
}

async function queueFileMentionSearch(): Promise<void> {
  if (!isFileMentionOpen.value) return
  const cwd = normalizeComposerPath(props.cwd ?? '')
  if (!cwd) {
    fileMentionSuggestions.value = []
    return
  }
  if (fileMentionDebounceTimer) {
    clearTimeout(fileMentionDebounceTimer)
  }
  const token = ++fileMentionSearchToken
  fileMentionDebounceTimer = setTimeout(async () => {
    try {
      const recentPaths = loadRecentMentionPaths(cwd)
      const rows = await searchComposerFiles(cwd, mentionQuery.value, 20, recentPaths)
      if (!isFileMentionOpen.value || token !== fileMentionSearchToken) return
      fileMentionSuggestions.value = rows
      fileMentionHighlightedIndex.value = 0
      const existingWarmRows = getWarmComposerSuggestionCacheEntry(cwd)?.rows ?? []
      setWarmComposerSuggestionCacheEntry(cwd, {
        rows: mentionQuery.value.trim().length === 0
          ? (existingWarmRows.length > rows.length ? existingWarmRows : rows)
          : (existingWarmRows.length > 0 ? existingWarmRows : rows),
        warmedAtMs: Date.now(),
        pending: null,
      })
    } catch {
      if (!isFileMentionOpen.value || token !== fileMentionSearchToken) return
      fileMentionSuggestions.value = []
    }
  }, mentionQuery.value.trim().length === 0 ? EMPTY_FILE_MENTION_DEBOUNCE_MS : FILE_MENTION_DEBOUNCE_MS)
}

function applyFileMention(suggestion: ComposerFileSuggestion): void {
  const input = inputRef.value
  const start = mentionStartIndex.value
  if (start !== null && input) {
    const cursor = input.selectionStart ?? draft.value.length
    draft.value = `${draft.value.slice(0, start)}${draft.value.slice(cursor)}`.trimEnd()
  }
  addFileAttachment(suggestion.path, undefined, suggestion.kind)
  rememberRecentMentionEntry({ path: suggestion.path, kind: suggestion.kind })
  closeFileMention()
  nextTick(() => input?.focus())
}

function hydrateDraft(payload: ComposerDraftPayload): void {
  cancelDictation()
  replaceDraftState(payload)
  nextTick(() => inputRef.value?.focus())
}

function getMentionFileName(path: string): string {
  const idx = path.lastIndexOf('/')
  if (idx < 0) return path
  return path.slice(idx + 1)
}

function getMentionDirName(path: string): string {
  const idx = path.lastIndexOf('/')
  if (idx <= 0) return ''
  return path.slice(0, idx)
}

function getFileExtension(path: string): string {
  const base = getMentionFileName(path)
  const idx = base.lastIndexOf('.')
  if (idx <= 0) return ''
  return base.slice(idx + 1).toLowerCase()
}

function getMentionBadgeText(path: string): string {
  const ext = getFileExtension(path)
  if (ext === 'ts') return 'TS'
  if (ext === 'tsx') return 'TSX'
  if (ext === 'js') return 'JS'
  if (ext === 'jsx') return 'JSX'
  if (ext === 'json') return '{}'
  return ''
}

function getMentionBadgeClass(path: string): string {
  const ext = getFileExtension(path)
  if (ext.startsWith('ts')) return 'ts'
  if (ext.startsWith('js')) return 'js'
  if (ext === 'json') return 'json'
  return 'default'
}

function isMarkdownFile(path: string): boolean {
  const ext = getFileExtension(path)
  return ext === 'md' || ext === 'mdx'
}

function onMenuOptionSelect(option: SkillItem | SlashCommandOption): void {
  if (menuMode.value === 'slash') {
    executeSlashCommand(option.path)
    return
  }

  const skill = option as SkillItem
  if (!selectedSkills.value.some((s) => s.path === skill.path)) {
    selectedSkills.value = [...selectedSkills.value, skill]
  }
  draft.value = draft.value.startsWith('$') ? '' : draft.value
  isSlashMenuOpen.value = false
  menuMode.value = null
  inputRef.value?.focus()
}

function parseSlashCommand(raw: string): string | null {
  const trimmed = raw.trim()
  if (!trimmed.startsWith('/')) return null
  const [command] = trimmed.slice(1).split(/\s+/, 1)
  return command ? command.toLowerCase() : null
}

function clearSlashDraftState(): void {
  if (props.activeThreadId && shouldPersistDraft.value) {
    clearPersistedDraftForThread(props.activeThreadId)
  }
  draft.value = ''
  isSlashMenuOpen.value = false
  menuMode.value = null
}

function executeSlashCommand(command: string): boolean {
  if (command === 'compact') {
    if (!showCompactButton.value || isThreadBusyComputed.value || props.disabled || !props.activeThreadId) return false
    clearSlashDraftState()
    emit('compact')
    nextTick(() => inputRef.value?.focus())
    return true
  }
  if (command === 'review') {
    if (!hasSelectedThreadContext.value) return false
    clearSlashDraftState()
    emit('slash-command', 'review')
    nextTick(() => inputRef.value?.focus())
    return true
  }
  if (command === 'fork') {
    if (!hasSelectedThreadContext.value) return false
    clearSlashDraftState()
    emit('slash-command', 'fork')
    nextTick(() => inputRef.value?.focus())
    return true
  }
  if (command === 'resume') {
    clearSlashDraftState()
    emit('slash-command', 'resume')
    nextTick(() => inputRef.value?.focus())
    return true
  }
  if (command === 'model') {
    if (!canUseGlobalSlashControls.value || props.models.length === 0) return false
    clearSlashDraftState()
    openModelPicker()
    return true
  }
  if (command === 'plan') {
    if (!canUseGlobalSlashControls.value) return false
    clearSlashDraftState()
    emit('update:selected-collaboration-mode', 'plan')
    nextTick(() => inputRef.value?.focus())
    return true
  }
  if (command === 'collab') {
    if (!canUseGlobalSlashControls.value) return false
    clearSlashDraftState()
    openCollaborationMenu()
    return true
  }
  if (command === 'status') {
    clearSlashDraftState()
    emit('slash-command', 'status')
    nextTick(() => inputRef.value?.focus())
    return true
  }
  if (command === 'mcp') {
    clearSlashDraftState()
    emit('slash-command', 'mcp')
    nextTick(() => inputRef.value?.focus())
    return true
  }
  return false
}

function tryExecuteSlashCommand(): boolean {
  if (isInlineEdit.value) return false
  const command = parseSlashCommand(draft.value)
  if (!command) return false
  return executeSlashCommand(command)
}

function onDocumentClick(event: MouseEvent): void {
  if (!isAttachMenuOpen.value) return
  const root = attachMenuRootRef.value
  if (!root) return
  const target = event.target as Node | null
  if (!target || root.contains(target)) return
  isAttachMenuOpen.value = false
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
  window.addEventListener('drop', onWindowDragCleanup)
  window.addEventListener('dragend', onWindowDragCleanup)
  window.addEventListener('blur', onWindowDragCleanup)
})

defineExpose<ThreadComposerExposed>({
  hydrateDraft,
  hasUnsavedDraft: () => hasUnsavedDraft.value,
  clearDraft: clearDraftState,
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
  window.removeEventListener('drop', onWindowDragCleanup)
  window.removeEventListener('dragend', onWindowDragCleanup)
  window.removeEventListener('blur', onWindowDragCleanup)
  window.removeEventListener('pointerup', onDictationPressEnd)
  window.removeEventListener('pointercancel', onDictationPressEnd)
  window.removeEventListener('blur', onDictationPressEnd)
  if (fileMentionDebounceTimer) {
    clearTimeout(fileMentionDebounceTimer)
  }
})

watch(
  () => props.activeThreadId,
  (nextThreadId) => {
    cancelDictation()
    if (lastActiveThreadId && shouldPersistDraft.value) {
      persistDraftForThread(lastActiveThreadId, getCurrentDraftPayload())
    }
    clearDraftState()
    if (shouldPersistDraft.value) {
      const restored = loadPersistedDraftForThread(nextThreadId)
      if (restored) {
        replaceDraftState(restored)
        onInputChange()
      }
    }
    lastActiveThreadId = nextThreadId.trim()
  },
  { immediate: true },
)

watch([draft, selectedImages, fileAttachments, selectedSkills], () => {
  if (!lastActiveThreadId || !shouldPersistDraft.value) return
  persistDraftForThread(lastActiveThreadId, getCurrentDraftPayload())
}, { deep: true })

watch(
  () => props.cwd,
  (nextCwd) => {
    const normalizedCwd = normalizeComposerPath(nextCwd ?? '')
    if (normalizedCwd) {
      void prewarmFileMentionSuggestions(normalizedCwd)
    }
    if (isFileMentionOpen.value) {
      void queueFileMentionSearch()
    }
  },
  { immediate: true },
)

watch(
  inProgressMode,
  (nextMode) => {
    activeInProgressMode.value = nextMode
  },
)


</script>

<style scoped>
@reference "tailwindcss";

.thread-composer {
  @apply w-full max-w-[min(var(--chat-column-max,72rem),100%)] mx-auto;
}

.thread-composer--inline-edit {
  @apply max-w-[min(46rem,100%)];
}

.thread-composer-shell {
  @apply relative rounded-2xl border border-zinc-300 bg-white p-2 sm:p-3 shadow-sm;
}

.thread-composer-shell--inline-edit {
  @apply rounded-xl border-amber-200 bg-amber-50/40 px-2.5 py-2 shadow-none;
}

.thread-composer-shell--drag-active {
  @apply border-zinc-900 shadow-md;
}

.thread-composer-shell--no-top-radius {
  @apply rounded-t-none border-t-0;
}

.thread-composer-attachments {
  @apply mb-2 flex flex-wrap gap-2;
}

.thread-composer-attachment {
  @apply relative h-14 w-14 overflow-hidden rounded-lg border border-zinc-200 bg-zinc-50;
}

.thread-composer-attachment-image {
  @apply h-full w-full object-cover;
}

.thread-composer-attachment-remove {
  @apply absolute right-0.5 top-0.5 inline-flex h-4 w-4 items-center justify-center rounded-full border-0 bg-black/70 text-xs leading-none text-white;
}

.thread-composer-file-chips {
  @apply mb-2 flex flex-wrap gap-1.5;
}

.thread-composer-folder-chips {
  @apply mb-2 flex flex-wrap gap-1.5;
}

.thread-composer-folder-chip {
  @apply inline-flex items-center gap-1 rounded-md border border-amber-200 bg-amber-50 px-2 py-0.5 text-xs text-amber-800;
}

.thread-composer-folder-chip-icon {
  @apply h-3.5 w-3.5 text-amber-600 shrink-0;
}

.thread-composer-folder-chip-name {
  @apply truncate max-w-40 font-medium;
}

.thread-composer-folder-chip-meta {
  @apply text-amber-700/90;
}

.thread-composer-folder-chip-remove {
  @apply ml-0.5 inline-flex h-3.5 w-3.5 items-center justify-center rounded-full border-0 bg-transparent text-amber-600 transition hover:bg-amber-200 hover:text-amber-800 text-xs leading-none p-0;
}

.thread-composer-file-chip {
  @apply inline-flex items-center gap-1 rounded-md border border-zinc-200 bg-zinc-50 px-2 py-0.5 text-xs text-zinc-700;
}

.thread-composer-file-chip-icon {
  @apply h-3.5 w-3.5 text-zinc-400 shrink-0;
}

.thread-composer-file-chip-icon--folder {
  @apply text-amber-600;
}

.thread-composer-file-chip-name {
  @apply truncate max-w-40 font-mono;
}

.thread-composer-file-chip-remove {
  @apply ml-0.5 inline-flex h-3.5 w-3.5 items-center justify-center rounded-full border-0 bg-transparent text-zinc-400 transition hover:bg-zinc-200 hover:text-zinc-700 text-xs leading-none p-0;
}

.thread-composer-skill-chips {
  @apply mb-2 flex flex-wrap gap-1.5;
}

.thread-composer-skill-chip {
  @apply inline-flex items-center gap-1 rounded-md border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700;
}

.thread-composer-skill-chip-name {
  @apply font-medium;
}

.thread-composer-skill-chip-remove {
  @apply ml-0.5 inline-flex h-3.5 w-3.5 items-center justify-center rounded-full border-0 bg-transparent text-emerald-500 transition hover:bg-emerald-200 hover:text-emerald-700 text-xs leading-none p-0;
}

.thread-composer-rate-limit {
  @apply mb-1.5 px-1 text-[11px] leading-5 text-zinc-500;
}

.thread-composer-rate-limit-row {
  @apply flex min-w-0 items-center gap-x-1.5 gap-y-1;
}

.thread-composer-rate-limit-value {
  @apply min-w-0 flex-1 truncate;
}

.thread-composer-context-usage-inline {
  --context-usage-accent: rgb(34 197 94);
  @apply ml-auto inline-flex min-w-0 max-w-[56%] items-center gap-2 text-right;
}

.thread-composer-context-usage-inline.is-warning {
  --context-usage-accent: rgb(245 158 11);
}

.thread-composer-context-usage-inline.is-danger {
  --context-usage-accent: rgb(239 68 68);
}

.thread-composer-context-usage-inline-value {
  @apply min-w-0 truncate font-medium tabular-nums;
  color: var(--context-usage-accent);
}

.thread-composer-context-usage-inline-bar {
  @apply block h-1.5 w-14 shrink-0 overflow-hidden rounded-full bg-zinc-200/80;
}

.thread-composer-context-usage-inline-bar-fill {
  @apply block h-full rounded-full transition-[width] duration-200 ease-out;
  background: var(--context-usage-accent);
}

.thread-composer-context-badge {
  @apply inline-flex h-7 shrink-0 items-center rounded-full border border-emerald-200 bg-emerald-50 px-2.5 text-xs font-semibold tabular-nums text-emerald-700;
}

.thread-composer-context-badge.is-warning {
  @apply border-amber-200 bg-amber-50 text-amber-700;
}

.thread-composer-context-badge.is-danger {
  @apply border-rose-200 bg-rose-50 text-rose-700;
}

.thread-composer-input-wrap {
  @apply relative;
}

.thread-composer-input-wrap--drag-active {
  @apply rounded-xl bg-zinc-50;
}

.thread-composer-drop-overlay {
  @apply pointer-events-none absolute inset-0 z-30 flex items-center justify-center rounded-xl border border-dashed border-zinc-900 bg-white/90;
}

.thread-composer-drop-overlay-copy {
  @apply rounded-full bg-zinc-900 px-3 py-1 text-xs font-medium text-white shadow-sm;
}

.thread-composer-file-mentions {
  @apply absolute left-0 right-0 bottom-[calc(100%+8px)] z-40 max-h-52 overflow-y-auto rounded-xl border border-zinc-200 bg-white p-1 shadow-lg;
}

.thread-composer-file-mentions-header {
  @apply px-2 pb-1.5 pt-1 text-[11px] text-zinc-500;
}

.thread-composer-file-mentions-title {
  @apply block font-medium text-zinc-700;
}

.thread-composer-file-mentions-hint {
  @apply mt-0.5 block;
}

.thread-composer-file-mention-row {
  @apply flex w-full items-center gap-2 rounded-md border-0 bg-transparent px-2 py-1.5 text-left text-xs text-zinc-700 transition hover:bg-zinc-100;
}

.thread-composer-file-mention-row.is-active {
  @apply bg-zinc-100;
}

.thread-composer-file-mention-icon-badge {
  @apply inline-flex h-5 min-w-5 items-center justify-center rounded px-1 text-[9px] font-semibold leading-none;
}

.thread-composer-file-mention-icon-badge.is-ts {
  @apply bg-zinc-700 text-white;
}

.thread-composer-file-mention-icon-badge.is-js {
  @apply bg-zinc-600 text-white;
}

.thread-composer-file-mention-icon-badge.is-json {
  @apply bg-zinc-600 text-white;
}

.thread-composer-file-mention-icon-markdown {
  @apply inline-flex h-5 min-w-5 items-center justify-center text-sm leading-none text-zinc-700;
}

.thread-composer-file-mention-icon-file {
  @apply h-4 w-4 text-zinc-600;
}

.thread-composer-file-mention-text {
  @apply min-w-0 flex items-baseline gap-2;
}

.thread-composer-file-mention-name {
  @apply truncate text-zinc-900;
}

.thread-composer-file-mention-dir {
  @apply truncate text-zinc-400;
}

.thread-composer-file-mention-empty {
  @apply px-2 py-1.5 text-xs text-zinc-500;
}

.thread-composer-input {
  @apply w-full min-w-0 min-h-10 sm:min-h-11 max-h-40 rounded-xl border-0 bg-transparent px-1 py-2 text-sm text-zinc-900 outline-none transition resize-none overflow-y-auto;
}

.thread-composer-input--inline-edit {
  @apply min-h-8 max-h-28 px-0 py-1.5 text-[13px] leading-5;
}

.thread-composer-input:focus {
  @apply ring-0;
}

.thread-composer-input:disabled {
  @apply bg-zinc-100 text-zinc-500 cursor-not-allowed;
}

.thread-composer-controls {
  @apply relative mt-2 sm:mt-3 flex items-center gap-2 sm:gap-4 overflow-visible;
}

.thread-composer-controls--inline-edit {
  @apply mt-1.5 gap-2;
}

.thread-composer-controls--recording {
  @apply gap-1 sm:gap-2;
}

.thread-composer-primary-controls {
  @apply min-w-0 flex flex-1 items-center gap-2 sm:gap-4;
}

.thread-composer-runtime-controls {
  @apply min-w-0 flex flex-1 items-center gap-2 sm:gap-4;
}

.thread-composer-meta-controls {
  @apply min-w-0 flex shrink-0 items-center gap-2;
}

.thread-composer-attach {
  @apply relative shrink-0;
}

.thread-composer-attach-trigger {
  @apply inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-none border-0 bg-transparent text-xl leading-none text-zinc-700 transition hover:text-zinc-900 disabled:cursor-not-allowed disabled:text-zinc-400;
}

.thread-composer-attach-menu {
  @apply absolute bottom-11 left-0 z-20 w-72 max-w-[calc(100vw-1rem)] rounded-xl border border-zinc-200 bg-white p-1 shadow-lg;
}

.thread-composer-attach-item {
  @apply block w-full rounded-lg border-0 bg-transparent px-3 py-2 text-left text-sm text-zinc-800 transition hover:bg-zinc-100 disabled:cursor-not-allowed disabled:text-zinc-400;
}

.thread-composer-attach-separator {
  @apply my-1 h-px bg-zinc-100;
}

.thread-composer-attach-mode {
  @apply px-3 py-2 flex items-center justify-between gap-2;
}

.thread-composer-attach-mode-label {
  @apply text-sm text-zinc-800;
}

.thread-composer-attach-mode-buttons {
  @apply inline-flex items-center rounded-full border border-zinc-200 bg-white p-0.5;
}

.thread-composer-attach-mode-button {
  @apply rounded-full border-0 bg-transparent px-2 py-1 text-xs text-zinc-600 transition hover:text-zinc-800 disabled:cursor-not-allowed disabled:text-zinc-400;
}

.thread-composer-attach-mode-button.is-active {
  @apply bg-zinc-900 text-white hover:text-white;
}

.thread-composer-attach-setting {
  @apply flex w-full items-center justify-between gap-3 rounded-lg border-0 bg-transparent px-3 py-2 text-left transition hover:bg-zinc-100 disabled:cursor-not-allowed disabled:text-zinc-400;
}

.thread-composer-attach-setting-copy {
  @apply min-w-0 flex flex-col;
}

.thread-composer-attach-setting-label {
  @apply text-sm text-zinc-800;
}

.thread-composer-attach-setting-description {
  @apply mt-0.5 text-xs text-zinc-500;
}

.thread-composer-attach-switch {
  @apply relative h-5 w-9 shrink-0 rounded-full bg-zinc-300 transition-colors;
}

.thread-composer-attach-switch::after {
  content: '';
  @apply absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-white transition-transform shadow-sm;
}

.thread-composer-attach-switch.is-on {
  @apply bg-emerald-600;
}

.thread-composer-attach-switch.is-on::after {
  transform: translateX(16px);
}

.thread-composer-attach-switch.is-busy {
  @apply opacity-70;
}

.thread-composer-attach-switch.is-disabled {
  @apply opacity-50;
}

.thread-composer-control {
  @apply shrink-1 min-w-0;
}

.thread-composer-control :deep(.composer-dropdown-value) {
  @apply truncate;
}

.thread-composer-command-button {
  @apply inline-flex h-7 shrink-0 items-center border-0 bg-transparent p-0 text-sm leading-none text-zinc-500 transition hover:text-zinc-800 disabled:cursor-not-allowed disabled:text-zinc-400;
}

.thread-composer-command-button.is-busy {
  @apply text-amber-700 hover:text-amber-700 disabled:text-amber-700;
}

.thread-composer-compact-status-badge {
  @apply inline-flex h-7 shrink-0 items-center rounded-full border border-amber-200 bg-amber-50 px-2.5 text-xs font-semibold text-amber-700;
}

.thread-composer-actions {
  @apply ml-auto flex min-w-0 items-center gap-2;
}

.thread-composer-actions--recording {
  @apply ml-0 flex-1;
}

.thread-composer-mic {
  @apply inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full border-0 bg-zinc-100 text-zinc-600 transition hover:bg-zinc-200 hover:text-zinc-900 disabled:cursor-not-allowed disabled:text-zinc-400;
  touch-action: none;
}

.thread-composer-mic--active {
  @apply bg-red-100 text-red-600 hover:bg-red-200 hover:text-red-700;
}

.thread-composer-mic-icon {
  @apply h-5 w-5;
}

.thread-composer-dictation-waveform-wrap {
  @apply min-w-0 flex-1;
}

.thread-composer-dictation-waveform {
  @apply block h-9 w-full text-zinc-500;
}

.thread-composer-dictation-timer {
  @apply shrink-0 text-sm text-zinc-500 tabular-nums;
}

.thread-composer-dictation-error {
  @apply mb-2 px-1 text-xs text-amber-700;
}

.thread-composer-submit {
  @apply inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full border-0 bg-zinc-900 text-white transition hover:bg-black disabled:cursor-not-allowed disabled:bg-zinc-200 disabled:text-zinc-500;
}

.thread-composer-submit--queue {
  @apply bg-amber-600 hover:bg-amber-700;
}

.thread-composer-submit-icon {
  @apply h-5 w-5;
}

.thread-composer-stop {
  @apply inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full border-0 bg-zinc-900 text-white transition hover:bg-black disabled:cursor-not-allowed disabled:bg-zinc-200 disabled:text-zinc-500;
}

.thread-composer-stop-icon {
  @apply h-5 w-5;
}

.thread-composer-hidden-input {
  @apply hidden;
}

@media (max-width: 639px) {
  .thread-composer-shell {
    @apply rounded-[1.6rem] border-zinc-200 bg-white/95 px-2 py-1.5 shadow-[0_10px_30px_rgba(15,23,42,0.08)];
    backdrop-filter: blur(12px);
  }

  .thread-composer-input {
    @apply min-h-9 max-h-28 px-0.5 py-1.5 text-[15px] leading-6;
  }

  .thread-composer-controls {
    @apply mt-1.5 flex-col items-stretch gap-2;
  }

  .thread-composer-primary-controls {
    @apply w-full flex-col items-stretch gap-2;
  }

  .thread-composer-runtime-controls {
    @apply grid w-full grid-cols-2 gap-2;
  }

  .thread-composer-meta-controls {
    @apply flex w-full items-center gap-2;
  }

  .thread-composer-attach {
    @apply order-2;
  }

  .thread-composer-attach-trigger {
    @apply h-9 w-9 rounded-full border border-zinc-200 bg-zinc-50 text-[22px] text-zinc-700 shadow-sm;
  }

  .thread-composer-attach-menu {
    left: 0;
    right: 0;
    bottom: calc(100% + 10px);
    width: auto;
    max-width: none;
  }

  .thread-composer-control {
    min-width: 0;
  }

  .thread-composer-control--skills {
    flex-basis: 100%;
  }

  .thread-composer-control :deep(.composer-dropdown),
  .thread-composer-control :deep(.search-dropdown) {
    @apply flex w-full min-w-0;
  }

  .thread-composer-control :deep(.composer-dropdown-trigger),
  .thread-composer-control :deep(.search-dropdown-trigger) {
    @apply h-9 w-full min-w-0 items-center justify-between rounded-2xl border border-zinc-200 bg-zinc-50 px-3 text-[13px] text-zinc-700 shadow-sm;
  }

  .thread-composer-control :deep(.composer-dropdown-value),
  .thread-composer-control :deep(.search-dropdown-value) {
    @apply min-w-0 truncate;
  }

  .thread-composer-control :deep(.composer-dropdown-chevron),
  .thread-composer-control :deep(.search-dropdown-chevron) {
    @apply h-4 w-4;
  }

  .thread-composer-command-button {
    @apply inline-flex h-8 shrink-0 items-center rounded-full border border-zinc-200 bg-zinc-50 px-3 text-[12px] font-medium text-zinc-700 shadow-sm;
  }

  .thread-composer-command-button.is-busy {
    @apply border-amber-200 bg-amber-50 text-amber-700;
  }

  .thread-composer-compact-status-badge {
    @apply h-8 px-2.5 text-[11px] shadow-sm;
  }

  .thread-composer-context-badge {
    @apply h-8 px-2.5 text-[11px] shadow-sm;
  }

  .thread-composer-actions {
    @apply ml-0 w-full justify-end gap-2 pt-0;
  }

  .thread-composer-mic,
  .thread-composer-submit,
  .thread-composer-stop {
    @apply h-10 w-10 shadow-sm;
  }
}
</style>
