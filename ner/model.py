import torch
import torch.nn as nn
from transformers import BertConfig
from ner.LBert import WCBertModel, BertPreTrainedModel
from ner.crf import CRF
from ner.model_with_bert import BiRnnCrf
from ICCSupervised.ICCSupervised import IModel


class BertNER(IModel):

    def __init__(self, bert_config_file_name, pretrained_file_name, pretrained_embeddings, tagset_size, hidden_dim):
        self.load_model(bert_config_file_name, pretrained_file_name,
                        pretrained_embeddings, tagset_size, hidden_dim)

    def load_model(self, bert_config_file_name, pretrained_file_name, pretrained_embeddings, tagset_size, hidden_dim):
        config = BertConfig.from_json_file(bert_config_file_name)
        self.model = LBertModel.from_pretrained(
            pretrained_file_name, pretrained_embeddings=pretrained_embeddings, config=config)
        self.birnncrf = BiRnnCrf(
            tagset_size=tagset_size, embedding_dim=config.hidden_size, hidden_dim=hidden_dim)

    def get_model(self):
        return self.model, self.birnncrf

    def __call__(self):
        return self.get_model()


class LBertModel(BertPreTrainedModel):
    '''
    config: BertConfig
    pretrained_embeddings: 预训练embeddings shape还没去看
    '''

    def __init__(self, config, pretrained_embeddings):
        super().__init__(config)

        word_vocab_size = pretrained_embeddings.shape[0]
        embed_dim = pretrained_embeddings.shape[1]
        self.word_embeddings = nn.Embedding(word_vocab_size, embed_dim)
        self.bert = WCBertModel(config)

        self.init_weights()

        # self.word_transform = nn.Linear(config.word_embed_dim, config.hidden_size)
        # self.act = nn.Tanh()
        # self.word_word_weight = nn.Linear(config.hidden_size, config.hidden_size)
        # self.dropout = nn.Dropout(config.HP_dropout)


        # attn_W = torch.zeros(config.hidden_size, config.hidden_size)
        # self.attn_W = nn.Parameter(attn_W)
        # self.attn_W.data.normal_(mean=0.0, std=config.initializer_range)

        # init the embedding
        self.word_embeddings.weight.data.copy_(
            torch.from_numpy(pretrained_embeddings))
        print("Load pretrained embedding from file.........")

    def forward(
            self,
            **args
    ):
        matched_word_embeddings = self.word_embeddings(
            args['matched_word_ids'])
        outputs = self.bert(
            input_ids=args['input_ids'],
            attention_mask=args['attention_mask'],
            token_type_ids=args['token_type_ids'],
            matched_word_embeddings=matched_word_embeddings,
            matched_word_mask=args['matched_word_mask']
        )

        sequence_output = outputs[0]

        # matched_word_embeddings = self.word_transform(matched_word_embeddings)
        # matched_word_embeddings = self.act(matched_word_embeddings)
        # matched_word_embeddings = self.word_word_weight(matched_word_embeddings)
        # matched_word_embeddings = self.dropout(matched_word_embeddings)

        # alpha = torch.matmul(sequence_output.unsqueeze(2), self.attn_W)  # [N, L, 1, D]
        # alpha = torch.matmul(alpha, torch.transpose(matched_word_embeddings, 2, 3))  # [N, L, 1, W]
        # alpha = alpha.squeeze()  # [N, L, W]
        # alpha = alpha + (1 - args['matched_word_mask'].float()) * (-2 ** 31 + 1)
        # alpha = torch.nn.Softmax(dim=-1)(alpha)  # [N, L, W]
        # alpha = alpha.unsqueeze(-1)  # [N, L, W, 1]
        # matched_word_embeddings = torch.sum(matched_word_embeddings * alpha, dim=2)  # [N, L, D]

        # ## concat the embedding [B, L, N, D], [B, L, N]
        # sequence_output = torch.cat((sequence_output, matched_word_embeddings), dim=-1)
        # sequence_output = self.dropout(sequence_output)

        return {
            'mix_output': sequence_output,
            'last_hidden_state': outputs.last_hidden_state,
            'pooler_output': outputs.pooler_output,
            'hidden_states': outputs.hidden_states,
            'attentions': outputs.attentions,
        }
