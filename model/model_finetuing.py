import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, TaskType, PeftModel
import evaluate
from datasets import Dataset as HFDataset
import wandb
from sklearn.model_selection import train_test_split
import json

# ===== 의료 데이터셋 클래스 =====
class MedicalQADataset(Dataset):
    """의료 Q&A 데이터셋"""
    
    def __init__(self, data_path: str, tokenizer, max_length: int = 512):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.data = self._load_data(data_path)
        
    def _load_data(self, data_path: str) -> List[Dict]:
        """데이터 로드 및 전처리"""
        with open(data_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        processed_data = []
        for item in raw_data:
            # 프롬프트 구성
            prompt = self._create_prompt(
                instruction=item['instruction'],
                context=item.get('context', ''),
                question=item['question']
            )
            
            processed_data.append({
                'input': prompt,
                'output': item['answer'],
                'metadata': {
                    'category': item.get('category', 'general'),
                    'difficulty': item.get('difficulty', 'medium')
                }
            })
        
        return processed_data
    
    def _create_prompt(self, instruction: str, context: str, question: str) -> str:
        """표준화된 프롬프트 생성"""
        prompt = f"""### 지시사항
{instruction}

### 의료 정보
{context}

### 질문
{question}

### 답변
"""
        return prompt
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        
        # 입력과 출력 결합
        full_text = item['input'] + item['output']
        
        # 토크나이징
        encoding = self.tokenizer(
            full_text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        # 라벨 생성 (입력 부분은 -100으로 마스킹)
        input_ids = encoding['input_ids'].squeeze()
        attention_mask = encoding['attention_mask'].squeeze()
        
        # 입력 길이 계산
        input_length = len(self.tokenizer.encode(item['input'], truncation=True))
        
        # 라벨 마스킹
        labels = input_ids.clone()
        labels[:input_length] = -100
        
        return {
            'input_ids': input_ids,
            'attention_mask': attention_mask,
            'labels': labels
        }

# ===== LoRA 파인튜닝 설정 =====
class MedicalModelTrainer:
    """의료 모델 학습기"""
    
    def __init__(self, 
                 base_model_name: str = "beomi/KoAlpaca-Polyglot-5.8B",
                 output_dir: str = "./models/medical-llm"):
        self.base_model_name = base_model_name
        self.output_dir = output_dir
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 모델과 토크나이저 초기화
        self.tokenizer = AutoTokenizer.from_pretrained(base_model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # 기본 모델 로드
        self.model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
    def prepare_lora_model(self):
        """LoRA 설정 및 모델 준비"""
        
        # LoRA 설정
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=16,  # LoRA rank
            lora_alpha=32,
            lora_dropout=0.1,
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],  # 타겟 모듈
            bias="none"
        )
        
        # LoRA 적용
        self.model = get_peft_model(self.model, lora_config)
        self.model.print_trainable_parameters()
        
        return self.model
    
    def create_training_args(self, num_epochs: int = 3):
        """학습 인자 생성"""
        
        return TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=4,
            per_device_eval_batch_size=4,
            gradient_accumulation_steps=4,
            gradient_checkpointing=True,
            warmup_ratio=0.1,
            learning_rate=5e-5,
            fp16=True,
            logging_steps=10,
            evaluation_strategy="steps",
            eval_steps=100,
            save_strategy="steps",
            save_steps=500,
            save_total_limit=3,
            load_best_model_at_end=True,
            report_to="wandb",
            run_name="medical-llm-finetuning"
        )
    
    def train(self, train_dataset: Dataset, eval_dataset: Dataset):
        """모델 학습"""
        
        # LoRA 모델 준비
        self.prepare_lora_model()
        
        # 학습 인자
        training_args = self.create_training_args()
        
        # 데이터 콜레이터
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False
        )
        
        # 트레이너 초기화
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator,
            tokenizer=self.tokenizer
        )
        
        # 학습 시작
        trainer.train()
        
        # 모델 저장
        trainer.save_model()
        self.tokenizer.save_pretrained(self.output_dir)
        
        return trainer

# ===== 의료 안전성 검증 =====
class MedicalSafetyValidator:
    """의료 응답 안전성 검증기"""
    
    def __init__(self):
        self.dangerous_patterns = [
            (r'자가\s*진단', '자가 진단 권유'),
            (r'의사\s*방문\s*불필요', '의료진 방문 회피 권유'),
            (r'약물\s*중단', '처방약 임의 중단 권유'),
            (r'민간\s*요법.*효과적', '검증되지 않은 치료법 권유')
        ]
        
        self.required_disclaimers = [
            "의료진과 상담",
            "전문의 진료",
            "정확한 진단"
        ]
        
    def validate_response(self, response: str) -> Dict[str, any]:
        """응답 안전성 검증"""
        
        issues = []
        score = 1.0
        
        # 위험 패턴 검사
        for pattern, description in self.dangerous_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                issues.append(f"위험 패턴 감지: {description}")
                score -= 0.3
        
        # 필수 면책 조항 확인
        disclaimer_found = False
        for disclaimer in self.required_disclaimers:
            if disclaimer in response:
                disclaimer_found = True
                break
        
        if not disclaimer_found:
            issues.append("의료 면책 조항 누락")
            score -= 0.2
        
        # 구체적인 용량 권고 검사
        dosage_pattern = r'\d+\s*(mg|ml|g|mcg).*하루.*\d+회'
        if re.search(dosage_pattern, response):
            issues.append("구체적인 용량 권고 포함 - 주의 필요")
            score -= 0.1
        
        return {
            'score': max(0, score),
            'is_safe': score >= 0.7,
            'issues': issues,
            'requires_review': len(issues) > 0
        }

# ===== 평가 메트릭 =====
class MedicalEvaluator:
    """의료 모델 평가기"""
    
    def __init__(self):
        self.bleu = evaluate.load("bleu")
        self.rouge = evaluate.load("rouge")
        self.bertscore = evaluate.load("bertscore")
        
    def evaluate_generation(self, predictions: List[str], 
                          references: List[str]) -> Dict[str, float]:
        """생성 품질 평가"""
        
        # BLEU 점수
        bleu_score = self.bleu.compute(
            predictions=predictions,
            references=[[ref] for ref in references]
        )
        
        # ROUGE 점수
        rouge_score = self.rouge.compute(
            predictions=predictions,
            references=references
        )
        
        # BERTScore
        bert_score = self.bertscore.compute(
            predictions=predictions,
            references=references,
            lang="ko"
        )
        
        return {
            'bleu': bleu_score['bleu'],
            'rouge1': rouge_score['rouge1'],
            'rouge2': rouge_score['rouge2'],
            'rougeL': rouge_score['rougeL'],
            'bertscore_f1': np.mean(bert_score['f1'])
        }
    
    def evaluate_medical_accuracy(self, qa_pairs: List[Dict]) -> Dict[str, float]:
        """의료 정확성 평가"""
        
        correct_facts = 0
        total_facts = 0
        
        for pair in qa_pairs:
            question = pair['question']
            predicted = pair['predicted_answer']
            reference = pair['reference_answer']
            
            # 핵심 의료 사실 추출 및 비교
            pred_facts = self._extract_medical_facts(predicted)
            ref_facts = self._extract_medical_facts(reference)
            
            # 정확도 계산
            for fact in ref_facts:
                total_facts += 1
                if self._fact_match(fact, pred_facts):
                    correct_facts += 1
        
        return {
            'medical_accuracy': correct_facts / total_facts if total_facts > 0 else 0,
            'total_facts_evaluated': total_facts
        }
    
    def _extract_medical_facts(self, text: str) -> List[str]:
        """텍스트에서 의료 사실 추출"""
        facts = []
        
        # 약물 정보 추출
        drug_pattern = r'(\w+)\s*(?:은|는)\s*([^.]+)(?:약물|약품|치료제)'
        facts.extend(re.findall(drug_pattern, text))
        
        # 용량 정보 추출
        dosage_pattern = r'(\d+)\s*(mg|g|ml).*(?:하루|일일)\s*(\d+)회'
        facts.extend(re.findall(dosage_pattern, text))
        
        # 부작용 정보 추출
        side_effect_pattern = r'부작용.*?(?:포함|있음|나타남)'
        facts.extend(re.findall(side_effect_pattern, text))
        
        return facts
    
    def _fact_match(self, fact: str, fact_list: List[str]) -> bool:
        """사실 매칭 확인"""
        for candidate in fact_list:
            # 유사도 기반 매칭 (간단한 구현)
            if fact.lower() in candidate.lower() or candidate.lower() in fact.lower():
                return True
        return False

# ===== 지속적 학습 파이프라인 =====
class ContinualLearningPipeline:
    """지속적 학습 파이프라인"""
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.feedback_buffer = []
        self.update_threshold = 100
        
    def collect_feedback(self, 
                        question: str, 
                        generated_answer: str,
                        feedback_score: float,
                        corrected_answer: Optional[str] = None):
        """사용자 피드백 수집"""
        
        feedback = {
            'timestamp': datetime.now().isoformat(),
            'question': question,
            'generated_answer': generated_answer,
            'feedback_score': feedback_score,
            'corrected_answer': corrected_answer
        }
        
        self.feedback_buffer.append(feedback)
        
        # 버퍼가 충분히 쌓이면 재학습 트리거
        if len(self.feedback_buffer) >= self.update_threshold:
            self.trigger_retraining()
    
    def trigger_retraining(self):
        """재학습 트리거"""
        logger.info(f"재학습 시작: {len(self.feedback_buffer)}개 피드백")
        
        # 고품질 피드백만 필터링
        quality_feedback = [
            fb for fb in self.feedback_buffer 
            if fb['feedback_score'] < 3 and fb['corrected_answer']
        ]
        
        if len(quality_feedback) < 20:
            logger.info("고품질 피드백 부족, 재학습 연기")
            return
        
        # 재학습 데이터 준비
        retrain_data = []
        for fb in quality_feedback:
            retrain_data.append({
                'instruction': "다음 질문에 대해 정확하고 안전한 의료 정보를 제공하세요.",
                'question': fb['question'],
                'answer': fb['corrected_answer']
            })
        
        # 재학습 실행
        self._execute_retraining(retrain_data)
        
        # 버퍼 초기화
        self.feedback_buffer = []
    
    def _execute_retraining(self, retrain_data: List[Dict]):
        """실제 재학습 실행"""
        # 기존 모델 로드
        model = AutoModelForCausalLM.from_pretrained(self.model_path)
        tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        
        # 재학습 데이터셋 생성
        dataset = MedicalQADataset(retrain_data, tokenizer)
        
        # 경량 재학습 (LoRA)
        trainer = MedicalModelTrainer(self.model_path)
        trainer.model = model
        
        # 짧은 에폭으로 재학습
        training_args = trainer.create_training_args(num_epochs=1)
        training_args.learning_rate = 1e-5  # 낮은 학습률
        
        # 재학습
        trainer.train(dataset, dataset)  # 실제로는 검증셋 분리 필요
        
        logger.info("재학습 완료")

# ===== 모델 배포 준비 =====
class ModelDeploymentPrep:
    """모델 배포 준비"""
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        
    def quantize_model(self, quantization_type: str = "int8"):
        """모델 양자화"""
        from transformers import BitsAndBytesConfig
        
        if quantization_type == "int8":
            quantization_config = BitsAndBytesConfig(
                load_in_8bit=True,
                bnb_8bit_compute_dtype=torch.float16
            )
        elif quantization_type == "int4":
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4"
            )
        else:
            raise ValueError(f"Unknown quantization type: {quantization_type}")
        
        # 양자화된 모델 로드
        model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            quantization_config=quantization_config,
            device_map="auto"
        )
        
        return model
    
    def optimize_for_inference(self, model):
        """추론 최적화"""
        model.eval()
        
        # 그래디언트 체크포인팅 비활성화
        model.gradient_checkpointing_disable()
        
        # 컴파일 (PyTorch 2.0+)
        if hasattr(torch, 'compile'):
            model = torch.compile(model)
        
        return model
    
    def create_model_card(self) -> Dict:
        """모델 카드 생성"""
        return {
            'model_name': 'Korean Medical LLM',
            'base_model': 'beomi/KoAlpaca-Polyglot-5.8B',
            'fine_tuning_method': 'LoRA',
            'training_data': {
                'sources': ['MIMIC-III (translated)', 'Korean FDA data', 'DrugBank'],
                'size': '100K QA pairs',
                'languages': ['Korean']
            },
            'intended_use': '의료 정보 제공 및 상담 보조',
            'limitations': [
                '의료진의 전문적 판단을 대체할 수 없음',
                '응급 상황에서 사용 불가',
                '개인의 특수한 의료 상황 고려 불가'
            ],
            'ethical_considerations': [
                '의료 정보의 정확성과 안전성 최우선',
                '환자 프라이버시 보호',
                '의료 윤리 준수'
            ]
        }

# ===== 메인 학습 실행 =====
def main():
    """메인 학습 파이프라인"""
    
    # Wandb 초기화
    wandb.init(project="medical-llm", name="korean-medical-chatbot")
    
    # 데이터 로드
    logger.info("데이터 로드 중...")
    train_data = json.load(open('./data/medical_qa_train.json', 'r', encoding='utf-8'))
    
    # 학습/검증 분할
    train_data, val_data = train_test_split(train_data, test_size=0.1, random_state=42)
    
    # 트레이너 초기화
    trainer = MedicalModelTrainer()
    
    # 데이터셋 생성
    train_dataset = MedicalQADataset('./data/medical_qa_train.json', trainer.tokenizer)
    val_dataset = MedicalQADataset('./data/medical_qa_val.json', trainer.tokenizer)
    
    # 학습 실행
    logger.info("모델 학습 시작...")
    trainer.train(train_dataset, val_dataset)
    
    # 평가
    logger.info("모델 평가 중...")
    evaluator = MedicalEvaluator()
    
    # 테스트 데이터로 평가
    test_questions = [
        "당뇨병 환자가 메트포르민을 복용할 때 주의사항은?",
        "고혈압과 당뇨가 있는 환자에게 적합한 혈압약은?",
        "아스피린과 와파린을 함께 복용해도 되나요?"
    ]
    
    # 안전성 검증
    safety_validator = MedicalSafetyValidator()
    
    for question in test_questions:
        # 응답 생성
        response = generate_response(trainer.model, trainer.tokenizer, question)
        
        # 안전성 검증
        safety_result = safety_validator.validate_response(response)
        
        logger.info(f"질문: {question}")
        logger.info(f"응답: {response}")
        logger.info(f"안전성 점수: {safety_result['score']}")
        
        if not safety_result['is_safe']:
            logger.warning(f"안전성 이슈: {safety_result['issues']}")
    
    # 배포 준비
    logger.info("배포 준비 중...")
    deployment_prep = ModelDeploymentPrep(trainer.output_dir)
    
    # 모델 양자화
    quantized_model = deployment_prep.quantize_model("int8")
    
    # 모델 카드 생성
    model_card = deployment_prep.create_model_card()
    with open(f"{trainer.output_dir}/model_card.json", 'w', encoding='utf-8') as f:
        json.dump(model_card, f, ensure_ascii=False, indent=2)
    
    logger.info("학습 완료!")

def generate_response(model, tokenizer, question: str) -> str:
    """응답 생성 헬퍼 함수"""
    prompt = f"""### 질문
{question}

### 답변
"""
    
    inputs = tokenizer(prompt, return_tensors="pt")
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )
    
    response = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
    return response

if __name__ == "__main__":
    main()