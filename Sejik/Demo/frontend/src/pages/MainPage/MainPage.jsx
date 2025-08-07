import React from "react";
import * as S from "./MainPage.style";
import { Link } from "react-router-dom";
import "animate.css/animate.min.css";
import { AnimationOnScroll } from "react-animation-on-scroll";
export default function MainPage() {
  return (
    <>
      <S.MainImg>
        <AnimationOnScroll animateIn="animate__fadeInUp" animateOnce={true}>
          <S.MainContainer>
            <S.MainTitle1>Dr. Watson</S.MainTitle1>
            <S.MainTitle2>— 당신의 복약 도우미이자 건강 파트너</S.MainTitle2>
          </S.MainContainer>
        </AnimationOnScroll>
      </S.MainImg>
      <S.IntroContainer>
        <AnimationOnScroll animateIn="animate__fadeInUp" animateOnce={true}>
          <S.IntroBox>
            현대 의료 현장에서 환자와 보호자가 느끼는 <b>가장 큰 불안</b>은 바로
            “이 약을 어떻게, 언제, 무엇과 함께 먹어야 할까?”입니다.
          </S.IntroBox>
          <S.IntroBox>
            <b>
              Dr.Watson은 처방 이후의 불확실함을 줄여주는 스마트 복약 챗봇
              서비스
            </b>
            로,
          </S.IntroBox>
          <S.IntroBox>
            의사에게 미처 물어보지 못했던 약 정보부터, 부작용, 음식/약물 조합,
            복약 스케줄까지 당신의 질문에 정확하고 친절하게 답해드립니다.
          </S.IntroBox>
        </AnimationOnScroll>
      </S.IntroContainer>
      <AnimationOnScroll animateIn="animate__fadeIn" animateOnce={true}>
        <S.IntroContainer2>
          <S.IntroBox>우리가 해결하고 싶은 문제</S.IntroBox>
          <S.TitleContainer>
            <S.TitleBox>
              처방 받은 약의 복용법과 금기사항을 잘 모를 때
            </S.TitleBox>
            <S.TitleBox>복용 중인 약이 많아 조합이 걱정될 때</S.TitleBox>
            <S.TitleBox>
              아이나 고령자의 약 복용을 정확히 관리하고 싶을 때
            </S.TitleBox>
            <S.TitleBox>
              의사와의 짧은 진료 시간 이후 정보가 부족할 때
            </S.TitleBox>
          </S.TitleContainer>
        </S.IntroContainer2>
      </AnimationOnScroll>
      <AnimationOnScroll animateIn="animate__fadeIn" animateOnce={true}>
        <S.IntroBox>Dr.Watson의 핵심 기능</S.IntroBox>
        <S.FeatureGrid>
          <S.FeatureCard>
            <h4>🔍 의료 문서/약 사진 업로드</h4>
            <p>
              처방전, 진단서, 약 포장 사진을 올리면 성분 분석과 복약 정보 제공
            </p>
          </S.FeatureCard>
          <S.FeatureCard>
            <h4>💊 약물 정보 요약</h4>
            <p>약의 효능, 복용법, 주의사항, 금기 음식/약물 자동 분석</p>
          </S.FeatureCard>
          <S.FeatureCard>
            <h4>🛡️ 기저 질환 기반 위험 알림</h4>
            <p>사용자가 선택한 질환에 따라 부작용 가능성 자동 안내</p>
          </S.FeatureCard>
          <S.FeatureCard>
            <h4>📅 복약 스케줄 & 알람 캘린더</h4>
            <p>복약 시간 알림, 복용 체크 기능으로 복약률 자동 기록</p>
          </S.FeatureCard>
          <S.FeatureCard>
            <h4>👨‍⚕️ 의사와 공유되는 복약 이력 캘린더</h4>
            <p>다음 진료 시 의사가 확인 가능한 복약 이력 공유 기능</p>
          </S.FeatureCard>
          <S.FeatureCard>
            <h4>🎙️ 음성 채팅 지원</h4>
            <p>Web Speech API 기반 실시간 음성 대화 (고령자/비문해자 대응)</p>
          </S.FeatureCard>
          <S.FeatureCard>
            <h4>🧠 메모 + 일정 자동 불러오기</h4>
            <p>접속 시 현재 시간, 오늘 일정, 사용자 메모 자동 표시</p>
          </S.FeatureCard>
        </S.FeatureGrid>
      </AnimationOnScroll>
      <AnimationOnScroll animateIn="animate__fadeInUp" animateOnce={true}>
        <S.IntroContainer3>
          <S.SpecialReasonContainer>
            <S.SpecialReasonTitle>Dr.Watson이 특별한 이유</S.SpecialReasonTitle>
            <S.SpecialReasonList>
              <S.SpecialReasonItem>
                AI 기반 분석 + 의학 지식 결합 → 단순 텍스트 분석을 넘어, 의학적
                금기 조합까지 검토
              </S.SpecialReasonItem>
              <S.SpecialReasonItem>
                개인 맞춤 복약 정보 제공 → 기저 질환, 복용 중인 약, 나이 등
                사용자 맞춤 안내
              </S.SpecialReasonItem>
              <S.SpecialReasonItem>
                사용자-의료진 연결 고리 → 실제 진료에 도움되는 복약 캘린더
                공유로 의사-환자 커뮤니케이션 강화
              </S.SpecialReasonItem>
              <S.SpecialReasonItem>
                음성 기반 인터페이스 제공 → 모바일과 고령자 사용성까지 고려한
                접근성 강화
              </S.SpecialReasonItem>
            </S.SpecialReasonList>
          </S.SpecialReasonContainer>
        </S.IntroContainer3>
      </AnimationOnScroll>
      <AnimationOnScroll animateIn="animate__fadeIn" animateOnce={true}>
        <S.IntroContainer3>
          <S.IntroBox>이런 분들께 추천합니다</S.IntroBox>
          <S.TitleContainer>
            <S.TitleBox>고령자 및 복합 질환자</S.TitleBox>
            <S.TitleBox>약 복용 지침을 쉽게 알고 싶은 보호자 </S.TitleBox>
            <S.TitleBox> 소통 시간이 부족한 외래 진료 환자</S.TitleBox>
            <S.TitleBox>약물 조합 부작용이 걱정되는 일반 사용자</S.TitleBox>
          </S.TitleContainer>
        </S.IntroContainer3>
      </AnimationOnScroll>
      <AnimationOnScroll animateIn="animate__fadeIn" animateOnce={true}>
        <S.IntroContainer3>
          <S.IntroBox>지금 Dr.Watson과 함께</S.IntroBox>
          <S.IntroBox>더 안전하고 정확한 복약 생활을 시작하세요.</S.IntroBox>
          <S.SendButton>
            <Link to={`/chat`}>Dr.Watson 시작하기</Link>
          </S.SendButton>
        </S.IntroContainer3>
      </AnimationOnScroll>
    </>
  );
}
