---
name: task-directory
description: Every Hugging Face task with its task page and model-listing URL, built in, so model research can jump straight to the right task without fetching anything. Grouped by category, plus task groups for needs that span tasks (transcription, video generation, embeddings, …). Use first for any "find a model for X", "which task is X", "show me the latest X models", "link to the HF task page for X" request; use hf-tasks --refresh only if this map looks out of date.
---

# Hugging Face task directory

The task map from [huggingface.co/tasks](https://huggingface.co/tasks) as of **2026-11-13**, 52 tasks. It ships with the plugin and is refreshed with each release, so use it as it is, with no fetch needed.

For each task:

- **Page:** `https://huggingface.co/tasks/<id>`, the explainer, with curated models, datasets, Spaces and metrics (only for tasks marked with a page).
- **Models:** `https://huggingface.co/models?pipeline_tag=<id>&sort=trending`. Swap the sort for `downloads`, `likes`, `created` or `modified`. Add `&search=<word>` or `&library=<lib>` to narrow it.
- **Datasets:** `https://huggingface.co/datasets?task_categories=task_categories:<id>`. Note the prefix: dataset filters carry it, model filters mostly don't. "none" means the Hub has no dataset category for that task.
- **Narrowing** (library, language, app, provider, model type, size, licence): build the URL with `hub-search-urls` / `scripts/hub-url.py`, which knows each parameter's prefix and how values combine.
- **API:** `https://huggingface.co/api/models?pipeline_tag=<id>&sort=trendingScore&limit=50`, or `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/hf-tasks.py" models <id>`.

## Is this map out of date?

Re-read it live with `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/hf-tasks.py" taxonomy --refresh` (see `hf-tasks`) when any of these holds:

- the user says so;
- a model's `pipeline_tag` isn't listed here;
- no task below fits the need;
- this map is more than about three months old (it is dated 2026-11-13).

A live read is saved in your data folder, and later reads use it.

## Task groups (needs that span tasks)

| Group | Tasks | For |
| --- | --- | --- |
| `transcription` | `automatic-speech-recognition`, `audio-text-to-text`, `any-to-any` | Speech to text: transcription, dictation, subtitles, voice typing. Dedicated ASR models… |
| `speech-synthesis` | `text-to-speech`, `text-to-audio`, `any-to-any` | Text to speech and voice generation. |
| `audio-enhancement` | `audio-to-audio`, `voice-activity-detection` | Clean, separate or transform audio: denoise, dereverb, source separation, voice… |
| `video-generation` | `text-to-video`, `image-to-video`, `image-text-to-video`, `video-to-video` | Make or change video. |
| `image-editing` | `image-to-image`, `image-text-to-image`, `mask-generation`, `image-segmentation` | Change an existing image with or without a prompt. |
| `document-understanding` | `image-text-to-text`, `document-question-answering`, `image-to-text`, `visual-document-retrieval` | Read documents, forms, screenshots and scans. |
| `embeddings-and-retrieval` | `feature-extraction`, `sentence-similarity`, `text-ranking`, `visual-document-retrieval` | Vectors and ranking for search and RAG. |
| `vision-language` | `image-text-to-text`, `video-text-to-text`, `visual-question-answering` | Models that look at images or video and answer in text. |

Search a whole group: `hf-tasks.py models <group> --sort trending`. For speech-to-text, use `transcription-model-research`.

## Text

| Task | Page | Models | Datasets | What it does |
| --- | --- | --- | --- | --- |
| `feature-extraction` | [page](https://huggingface.co/tasks/feature-extraction) | [models](https://huggingface.co/models?pipeline_tag=feature-extraction&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:feature-extraction&sort=trending) | Feature extraction is the task of extracting features learnt in a model. |
| `fill-mask` | [page](https://huggingface.co/tasks/fill-mask) | [models](https://huggingface.co/models?pipeline_tag=fill-mask&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:fill-mask&sort=trending) | Masked language modeling is the task of masking some of the words in a sentence and predicting which words… |
| `question-answering` | [page](https://huggingface.co/tasks/question-answering) | [models](https://huggingface.co/models?pipeline_tag=question-answering&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:question-answering&sort=trending) | Question Answering models can retrieve the answer to a question from a given text, which is useful for… |
| `sentence-similarity` | [page](https://huggingface.co/tasks/sentence-similarity) | [models](https://huggingface.co/models?pipeline_tag=sentence-similarity&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:sentence-similarity&sort=trending) | Sentence Similarity is the task of determining how similar two texts are. Sentence similarity models convert… |
| `summarization` | [page](https://huggingface.co/tasks/summarization) | [models](https://huggingface.co/models?pipeline_tag=summarization&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:summarization&sort=trending) | Summarization is the task of producing a shorter version of a document while preserving its important… |
| `table-question-answering` | [page](https://huggingface.co/tasks/table-question-answering) | [models](https://huggingface.co/models?pipeline_tag=table-question-answering&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:table-question-answering&sort=trending) | Table Question Answering (Table QA) is the answering a question about an information on a given table. |
| `text-classification` | [page](https://huggingface.co/tasks/text-classification) | [models](https://huggingface.co/models?pipeline_tag=text-classification&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:text-classification&sort=trending) | Text Classification is the task of assigning a label or class to a given text. Some use cases are sentiment… |
| `text-generation` | [page](https://huggingface.co/tasks/text-generation) | [models](https://huggingface.co/models?pipeline_tag=text-generation&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:text-generation&sort=trending) | Generating text is the task of generating new text given another text. These models can, for example, fill in… |
| `text-ranking` | [page](https://huggingface.co/tasks/text-ranking) | [models](https://huggingface.co/models?pipeline_tag=text-ranking&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:text-ranking&sort=trending) | Text Ranking is the task of ranking a set of texts based on their relevance to a query. Text ranking models… |
| `token-classification` | [page](https://huggingface.co/tasks/token-classification) | [models](https://huggingface.co/models?pipeline_tag=token-classification&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:token-classification&sort=trending) | Token classification is a natural language understanding task in which a label is assigned to some tokens in… |
| `translation` | [page](https://huggingface.co/tasks/translation) | [models](https://huggingface.co/models?pipeline_tag=translation&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:translation&sort=trending) | Translation is the task of converting text from one language to another. |
| `zero-shot-classification` | [page](https://huggingface.co/tasks/zero-shot-classification) | [models](https://huggingface.co/models?pipeline_tag=zero-shot-classification&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:zero-shot-classification&sort=trending) | Zero-shot text classification is a task in natural language processing where a model is trained on a set of… |

## Vision

| Task | Page | Models | Datasets | What it does |
| --- | --- | --- | --- | --- |
| `depth-estimation` | [page](https://huggingface.co/tasks/depth-estimation) | [models](https://huggingface.co/models?pipeline_tag=depth-estimation&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:depth-estimation&sort=trending) | Depth estimation is the task of predicting depth of the objects present in an image. |
| `image-classification` | [page](https://huggingface.co/tasks/image-classification) | [models](https://huggingface.co/models?pipeline_tag=image-classification&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:image-classification&sort=trending) | Image classification is the task of assigning a label or class to an entire image. Images are expected to… |
| `image-feature-extraction` | [page](https://huggingface.co/tasks/image-feature-extraction) | [models](https://huggingface.co/models?pipeline_tag=image-feature-extraction&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:image-feature-extraction&sort=trending) | Image feature extraction is the task of extracting features learnt in a computer vision model. |
| `image-segmentation` | [page](https://huggingface.co/tasks/image-segmentation) | [models](https://huggingface.co/models?pipeline_tag=image-segmentation&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:image-segmentation&sort=trending) | Image Segmentation divides an image into segments where each pixel in the image is mapped to an object. This… |
| `image-to-3d` | [page](https://huggingface.co/tasks/image-to-3d) | [models](https://huggingface.co/models?pipeline_tag=image-to-3d&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:image-to-3d&sort=trending) | Image-to-3D models take in image input and produce 3D output. |
| `image-to-image` | [page](https://huggingface.co/tasks/image-to-image) | [models](https://huggingface.co/models?pipeline_tag=image-to-image&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:image-to-image&sort=trending) | Image-to-image is the task of transforming an input image through a variety of possible manipulations and… |
| `image-to-text` | [page](https://huggingface.co/tasks/image-to-text) | [models](https://huggingface.co/models?pipeline_tag=image-to-text&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:image-to-text&sort=trending) | Image to text models output a text from a given image. Image captioning or optical character recognition can… |
| `image-to-video` | [page](https://huggingface.co/tasks/image-to-video) | [models](https://huggingface.co/models?pipeline_tag=image-to-video&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:image-to-video&sort=trending) | Image-to-video models take a still image as input and generate a video. These models can be guided by text… |
| `keypoint-detection` | [page](https://huggingface.co/tasks/keypoint-detection) | [models](https://huggingface.co/models?pipeline_tag=keypoint-detection&sort=trending) | none | Keypoint detection is the task of identifying meaningful distinctive points or features in an image. |
| `mask-generation` | [page](https://huggingface.co/tasks/mask-generation) | [models](https://huggingface.co/models?pipeline_tag=mask-generation&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:mask-generation&sort=trending) | Mask generation is the task of generating masks that identify a specific object or region of interest in a… |
| `object-detection` | [page](https://huggingface.co/tasks/object-detection) | [models](https://huggingface.co/models?pipeline_tag=object-detection&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:object-detection&sort=trending) | Object Detection models allow users to identify objects of certain defined classes. Object detection models… |
| `text-to-3d` | [page](https://huggingface.co/tasks/text-to-3d) | [models](https://huggingface.co/models?pipeline_tag=text-to-3d&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:text-to-3d&sort=trending) | Text-to-3D models take in text input and produce 3D output. |
| `text-to-image` | [page](https://huggingface.co/tasks/text-to-image) | [models](https://huggingface.co/models?pipeline_tag=text-to-image&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:text-to-image&sort=trending) | Text-to-image is the task of generating images from input text. These pipelines can also be used to modify… |
| `text-to-video` | [page](https://huggingface.co/tasks/text-to-video) | [models](https://huggingface.co/models?pipeline_tag=text-to-video&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:text-to-video&sort=trending) | Text-to-video models can be used in any application that requires generating consistent sequence of images… |
| `unconditional-image-generation` | [page](https://huggingface.co/tasks/unconditional-image-generation) | [models](https://huggingface.co/models?pipeline_tag=unconditional-image-generation&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:unconditional-image-generation&sort=trending) | Unconditional image generation is the task of generating images with no condition in any context (like a… |
| `video-classification` | [page](https://huggingface.co/tasks/video-classification) | [models](https://huggingface.co/models?pipeline_tag=video-classification&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:video-classification&sort=trending) | Video classification is the task of assigning a label or class to an entire video. Videos are expected to… |
| `video-to-video` | [page](https://huggingface.co/tasks/video-to-video) | [models](https://huggingface.co/models?pipeline_tag=video-to-video&sort=trending) | none | Video-to-video models take one or more videos as input and generate new videos as output. They can enhance… |
| `zero-shot-image-classification` | [page](https://huggingface.co/tasks/zero-shot-image-classification) | [models](https://huggingface.co/models?pipeline_tag=zero-shot-image-classification&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:zero-shot-image-classification&sort=trending) | Zero-shot image classification is the task of classifying previously unseen classes during training of a… |
| `zero-shot-object-detection` | [page](https://huggingface.co/tasks/zero-shot-object-detection) | [models](https://huggingface.co/models?pipeline_tag=zero-shot-object-detection&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:zero-shot-object-detection&sort=trending) | Zero-shot object detection is a computer vision task to detect objects and their classes in images, without… |

## Audio

| Task | Page | Models | Datasets | What it does |
| --- | --- | --- | --- | --- |
| `audio-classification` | [page](https://huggingface.co/tasks/audio-classification) | [models](https://huggingface.co/models?pipeline_tag=audio-classification&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:audio-classification&sort=trending) | Audio classification is the task of assigning a label or class to a given audio. It can be used for… |
| `audio-to-audio` | [page](https://huggingface.co/tasks/audio-to-audio) | [models](https://huggingface.co/models?pipeline_tag=audio-to-audio&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:audio-to-audio&sort=trending) | Audio-to-Audio is a family of tasks in which the input is an audio and the output is one or multiple… |
| `automatic-speech-recognition` | [page](https://huggingface.co/tasks/automatic-speech-recognition) | [models](https://huggingface.co/models?pipeline_tag=automatic-speech-recognition&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:automatic-speech-recognition&sort=trending) | Automatic Speech Recognition (ASR), also known as Speech to Text (STT), is the task of transcribing a given… |
| `text-to-audio` | none | [models](https://huggingface.co/models?pipeline_tag=text-to-audio&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:text-to-audio&sort=trending) | Text-to-Audio |
| `text-to-speech` | [page](https://huggingface.co/tasks/text-to-speech) | [models](https://huggingface.co/models?pipeline_tag=text-to-speech&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:text-to-speech&sort=trending) | Text-to-Speech (TTS) is the task of generating natural sounding speech given text input. TTS models can be… |
| `voice-activity-detection` | none | [models](https://huggingface.co/models?pipeline_tag=voice-activity-detection&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:voice-activity-detection&sort=trending) | Voice Activity Detection |

## Multimodal

| Task | Page | Models | Datasets | What it does |
| --- | --- | --- | --- | --- |
| `any-to-any` | [page](https://huggingface.co/tasks/any-to-any) | [models](https://huggingface.co/models?pipeline_tag=any-to-any&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:any-to-any&sort=trending) | Any-to-any models can understand two or more modalities and output two or more modalities. |
| `audio-text-to-text` | [page](https://huggingface.co/tasks/audio-text-to-text) | [models](https://huggingface.co/models?pipeline_tag=audio-text-to-text&sort=trending) | none | Audio-text-to-text models take both an audio clip and a text prompt as input, and generate natural language… |
| `document-question-answering` | [page](https://huggingface.co/tasks/document-question-answering) | [models](https://huggingface.co/models?pipeline_tag=document-question-answering&sort=trending) | none | Document Question Answering (also known as Document Visual Question Answering) is the task of answering… |
| `image-text-to-image` | [page](https://huggingface.co/tasks/image-text-to-image) | [models](https://huggingface.co/models?pipeline_tag=image-text-to-image&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:image-text-to-image&sort=trending) | Image-text-to-image models take an image and a text prompt as input and generate a new image based on the… |
| `image-text-to-text` | [page](https://huggingface.co/tasks/image-text-to-text) | [models](https://huggingface.co/models?pipeline_tag=image-text-to-text&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:image-text-to-text&sort=trending) | Image-text-to-text models take in an image and text prompt and output text. These models are also called… |
| `image-text-to-video` | [page](https://huggingface.co/tasks/image-text-to-video) | [models](https://huggingface.co/models?pipeline_tag=image-text-to-video&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:image-text-to-video&sort=trending) | Image-text-to-video models take an reference image and a text instructions as and generate a video based on… |
| `video-text-to-text` | [page](https://huggingface.co/tasks/video-text-to-text) | [models](https://huggingface.co/models?pipeline_tag=video-text-to-text&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:video-text-to-text&sort=trending) | Video-text-to-text models take in a video and a text prompt and output text. These models are also called… |
| `visual-document-retrieval` | [page](https://huggingface.co/tasks/visual-document-retrieval) | [models](https://huggingface.co/models?pipeline_tag=visual-document-retrieval&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:visual-document-retrieval&sort=trending) | Visual document retrieval is the task of searching for relevant image-based documents, such as PDFs. These… |
| `visual-question-answering` | [page](https://huggingface.co/tasks/visual-question-answering) | [models](https://huggingface.co/models?pipeline_tag=visual-question-answering&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:visual-question-answering&sort=trending) | Visual Question Answering is the task of answering open-ended questions based on an image. They output… |

## Tabular

| Task | Page | Models | Datasets | What it does |
| --- | --- | --- | --- | --- |
| `tabular-classification` | [page](https://huggingface.co/tasks/tabular-classification) | [models](https://huggingface.co/models?pipeline_tag=tabular-classification&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:tabular-classification&sort=trending) | Tabular classification is the task of classifying a target category (a group) based on set of attributes. |
| `tabular-regression` | [page](https://huggingface.co/tasks/tabular-regression) | [models](https://huggingface.co/models?pipeline_tag=tabular-regression&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:tabular-regression&sort=trending) | Tabular regression is the task of predicting a numerical value given a set of attributes. |
| `time-series-forecasting` | none | [models](https://huggingface.co/models?pipeline_tag=time-series-forecasting&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:time-series-forecasting&sort=trending) | Time Series Forecasting |

## Reinforcement learning

| Task | Page | Models | Datasets | What it does |
| --- | --- | --- | --- | --- |
| `reinforcement-learning` | [page](https://huggingface.co/tasks/reinforcement-learning) | [models](https://huggingface.co/models?pipeline_tag=reinforcement-learning&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:reinforcement-learning&sort=trending) | Reinforcement learning is the computational approach of learning from action by interacting with an… |
| `robotics` | none | [models](https://huggingface.co/models?pipeline_tag=robotics&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:robotics&sort=trending) | Robotics |

## Other

| Task | Page | Models | Datasets | What it does |
| --- | --- | --- | --- | --- |
| `graph-ml` | none | [models](https://huggingface.co/models?pipeline_tag=graph-ml&sort=trending) | [datasets](https://huggingface.co/datasets?task_categories=task_categories:graph-ml&sort=trending) | Graph Machine Learning |

## Data storage

Reads nothing and writes nothing. This file is generated by `scripts/build-task-directory.py` from `data/tasks-snapshot.json` and `data/hf-urls/hf-urls.json`.
