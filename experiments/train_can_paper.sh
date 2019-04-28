# export CUDA_VISIBLE_DEVICES=0 # edit this if you want to limit yourself to GPU
export PYTHONPATH="slim/:$PYTHONPATH"
python3 main.py \
--learning_rate .0001 \
--can True \
--crop False \
--batch_size 16 \
--beta 0.5 \
--dataset wikiart \
--epoch 25 \
--input_fname_pattern */*.jpg \
--input_height 256 \
--lambda_val 1.0 \
--output_height 256 \
--sample_size 16 \
--smoothing 1.0 \
--train \
--use_resize True \
--visualize False \
