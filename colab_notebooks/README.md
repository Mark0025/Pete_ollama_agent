# 🚀 Google Colab GPU Testing Setup

## Quick Start

1. **Open in Colab**:

   - Upload `PeteOllama_GPU_Testing.ipynb` to Google Colab
   - Go to `Runtime` → `Change runtime type` → Select **GPU** → Save

2. **Expected Results**:

   - **GPU verification**: Should show Tesla T4/P100/V100
   - **Model download**: ~2-5 minutes (vs ~4 minutes locally)
   - **Load time**: 10-30 seconds (vs 8m31s locally)
   - **Inference speed**: 20-50 tokens/s (vs 0.06 tokens/s locally)
   - **API response**: 1-5 seconds (vs timeouts locally)

3. **If you want external access** (optional):
   - Sign up at [ngrok.com](https://ngrok.com) for auth token
   - Uncomment the ngrok section in cell 7
   - Add your auth token: `ngrok.set_auth_token("your_token_here")`

## Performance Goals

| Metric       | Local CPU     | Target GPU |
| ------------ | ------------- | ---------- |
| Load Time    | 8m31s         | 10-30s     |
| API Response | 300s+ timeout | 1-5s       |
| Tokens/sec   | 0.06-0.16     | 20-50      |

## Next Steps

After successful GPU testing:

1. **Extract training data** with `extract_jamie_data.py`
2. **Create custom model** using `pete.db` conversations
3. **Connect to VAPI** for voice interface
4. **Deploy to Azure** for production

## Troubleshooting

- **No GPU assigned**: Try Runtime → Restart and run again
- **Docker errors**: Rerun the Docker installation cell
- **Model timeout**: The 7B model is large; wait for full download
- **API timeouts**: Ensure model is loaded first with the interactive test

---

**Ready to test?** Upload the notebook and run each cell sequentially! 🎯
