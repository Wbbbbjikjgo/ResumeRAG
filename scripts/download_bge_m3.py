"""从 ModelScope 按需下载 BGE-M3 必需文件（跳过 onnx/sparse 等冗余权重）。"""

from modelscope.hub.file_download import model_file_download

FILES = [
    "config.json",
    "pytorch_model.bin",
    "sentencepiece.bpe.model",
    "tokenizer.json",
    "special_tokens_map.json",
    "config_sentence_transformers.json",
    "modules.json",
    "sentence_bert_config.json",
    "pooling_config.json",
]

for f in FILES:
    try:
        p = model_file_download("BAAI/bge-m3", f, cache_dir="models")
        print("OK:", f, "->", p)
    except Exception as e:
        print("SKIP:", f, "(", type(e).__name__, ")")

print("ALL DONE")
