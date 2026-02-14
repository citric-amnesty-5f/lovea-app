"""
AI Service: OpenAI GPT-4 integration for matchmaking and profile enhancement
"""
import openai
import os
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Profile, AILog
from app.schemas import AIMatchResponse, AIBioResponse

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY", "")

# Model configuration
GPT_MODEL = "gpt-5-nano"  # Released Aug 2025 | $0.05/1M input tokens, $0.40/1M output | 400K context window
TEMPERATURE = 0.7
MAX_TOKENS = 1000


class AIService:
    """AI Service for matchmaking and profile enhancement"""

    def __init__(self, db: Session):
        self.db = db

    # ========================================================================
    # Matchmaking
    # ========================================================================

    async def calculate_compatibility(
        self,
        profile1: Profile,
        profile2: Profile
    ) -> Tuple[float, List[str], List[str]]:
        """
        Calculate AI-powered compatibility score between two profiles.
        Falls back to rule-based scoring if OpenAI is unavailable.

        Returns:
            Tuple of (score, reasons, conversation_starters)
        """
        # Check if OpenAI API key is configured
        if not openai.api_key or openai.api_key.startswith("sk-your"):
            return self._fallback_compatibility(profile1, profile2)

        try:
            # Build prompt
            prompt = self._build_compatibility_prompt(profile1, profile2)

            # Call OpenAI API
            response = await self._call_openai(
                prompt=prompt,
                system_message="You are an expert relationship compatibility analyst for a dating app. Provide thoughtful, honest assessments.",
                user_id=profile1.user_id,
                operation="compatibility_analysis"
            )

            # Parse response
            result = self._parse_compatibility_response(response)

            return result['score'], result['reasons'], result['ice_breakers']
        except Exception as e:
            print(f"OpenAI compatibility analysis failed, using fallback: {e}")
            return self._fallback_compatibility(profile1, profile2)

    def _build_compatibility_prompt(self, profile1: Profile, profile2: Profile) -> str:
        """Build prompt for compatibility analysis"""

        # Calculate ages
        age1 = self._calculate_age(profile1.date_of_birth)
        age2 = self._calculate_age(profile2.date_of_birth)

        # Get interests
        interests1 = [i.name for i in profile1.interests] if profile1.interests else []
        interests2 = [i.name for i in profile2.interests] if profile2.interests else []

        prompt = f"""Analyze the compatibility between these two dating profiles and provide a detailed assessment.

Profile 1:
- Name: {profile1.name}
- Age: {age1}
- Gender: {profile1.gender.value}
- Bio: {profile1.bio or "Not provided"}
- Occupation: {profile1.occupation or "Not provided"}
- Interests: {', '.join(interests1) if interests1 else "Not provided"}
- Location: {profile1.location or "Not provided"}

Profile 2:
- Name: {profile2.name}
- Age: {age2}
- Gender: {profile2.gender.value}
- Bio: {profile2.bio or "Not provided"}
- Occupation: {profile2.occupation or "Not provided"}
- Interests: {', '.join(interests2) if interests2 else "Not provided"}
- Location: {profile2.location or "Not provided"}

Please provide your analysis in the following JSON format:
{{
    "score": <number between 0-100>,
    "reasons": [
        "<specific reason why they're compatible>",
        "<another reason>",
        "<one more reason>"
    ],
    "ice_breakers": [
        "<personalized conversation starter based on shared interests>",
        "<another conversation starter>",
        "<a third conversation starter>"
    ]
}}

Focus on:
1. Shared interests and hobbies
2. Personality compatibility based on bios
3. Life stage and goals alignment
4. Conversational chemistry potential

Be specific, thoughtful, and encouraging while being honest."""

        return prompt

    async def batch_compatibility_analysis(
        self,
        user_profile: Profile,
        candidate_profiles: List[Profile]
    ) -> List[AIMatchResponse]:
        """
        Analyze compatibility between user and multiple candidates

        Returns:
            List of AIMatchResponse with scores and reasons
        """
        results = []

        for candidate in candidate_profiles:
            score, reasons, ice_breakers = await self.calculate_compatibility(
                user_profile,
                candidate
            )

            results.append(AIMatchResponse(
                profile_id=candidate.id,
                compatibility_score=score,
                reasons=reasons,
                conversation_starters=ice_breakers
            ))

        # Sort by compatibility score
        results.sort(key=lambda x: x.compatibility_score, reverse=True)

        return results

    # ========================================================================
    # Bio Generation
    # ========================================================================

    async def generate_bio_suggestions(
        self,
        name: str,
        age: int,
        gender: str,
        occupation: Optional[str],
        interests: List[str],
        personality_traits: Optional[List[str]] = None
    ) -> AIBioResponse:
        """
        Generate AI bio suggestions

        Returns:
            AIBioResponse with bio suggestions, score, and tips
        """
        prompt = f"""Generate 3 creative, engaging dating profile bios for:

Name: {name}
Age: {age}
Gender: {gender}
Occupation: {occupation or "Not specified"}
Interests: {', '.join(interests) if interests else "various activities"}
Personality: {', '.join(personality_traits) if personality_traits else "friendly and open"}

Requirements:
- Each bio should be 2-3 sentences
- Showcase personality and interests
- Be authentic and appealing
- Avoid clichés like "love to laugh" or "looking for my partner in crime"
- Include a conversation hook

Also provide:
- A quality score (0-100) for how well the bio represents this person
- 3 tips for improving their profile

Respond in this JSON format:
{{
    "bio_suggestions": [
        "<first bio option>",
        "<second bio option>",
        "<third bio option>"
    ],
    "bio_score": <number 0-100>,
    "tips": [
        "<specific tip for profile improvement>",
        "<another tip>",
        "<third tip>"
    ]
}}"""

        try:
            response = await self._call_openai(
                prompt=prompt,
                system_message="You are a creative dating profile expert who writes engaging, authentic bios.",
                user_id=None,
                operation="bio_generation"
            )

            result = json.loads(response)

            return AIBioResponse(
                bio_suggestions=result['bio_suggestions'],
                bio_score=result['bio_score'],
                tips=result['tips']
            )

        except Exception as e:
            print(f"AI bio generation error: {str(e)}")
            # Fallback bios
            return AIBioResponse(
                bio_suggestions=[
                    f"{occupation or 'Professional'} who loves {interests[0] if interests else 'new experiences'}. Always up for an adventure!",
                    f"Passionate about {interests[0] if interests else 'life'} and good conversations. Let's grab coffee!",
                    f"{age}-year-old {gender} seeking meaningful connections. I enjoy {interests[0] if interests else 'exploring new things'}."
                ],
                bio_score=60,
                tips=[
                    "Add more specific details about your interests",
                    "Include a conversation starter or question",
                    "Show your personality and humor"
                ]
            )

    # ========================================================================
    # Conversation Starters
    # ========================================================================

    async def generate_ice_breakers(
        self,
        profile1: Profile,
        profile2: Profile
    ) -> List[str]:
        """Generate personalized ice breaker messages"""

        interests1 = [i.name for i in profile1.interests] if profile1.interests else []
        interests2 = [i.name for i in profile2.interests] if profile2.interests else []

        shared_interests = set(interests1) & set(interests2)

        prompt = f"""Generate 3 personalized ice breaker messages for {profile1.name} to send to {profile2.name} on a dating app.

{profile1.name}'s interests: {', '.join(interests1) if interests1 else "Not specified"}
{profile2.name}'s interests: {', '.join(interests2) if interests2 else "Not specified"}
{profile2.name}'s bio: {profile2.bio or "Not provided"}

Shared interests: {', '.join(shared_interests) if shared_interests else "None obvious"}

Requirements:
- Be friendly and engaging
- Reference their profile or shared interests
- Ask an open-ended question
- Keep it casual and authentic
- 1-2 sentences each

Respond with a JSON array of 3 ice breakers:
{{
    "ice_breakers": [
        "<first message>",
        "<second message>",
        "<third message>"
    ]
}}"""

        # Check if OpenAI API key is configured
        if not openai.api_key or openai.api_key.startswith("sk-your"):
            # Use fallback ice breakers directly
            if shared_interests:
                interest = list(shared_interests)[0]
                return [
                    f"Hey {profile2.name}! I noticed we both love {interest}. What got you into it?",
                    f"Hi! I see you're into {interest} too. Have any recommendations?",
                    f"Hey! Fellow {interest} enthusiast here. What's your favorite thing about it?"
                ]
            else:
                return [
                    f"Hey {profile2.name}! Your profile caught my attention. How's your week going?",
                    f"Hi {profile2.name}! I'd love to get to know you better. What do you like to do for fun?",
                    f"Hey! I thought we might click. Tell me something interesting about yourself!"
                ]

        try:
            response = await self._call_openai(
                prompt=prompt,
                system_message="You are a dating conversation expert who creates engaging, personalized ice breakers.",
                user_id=profile1.user_id,
                operation="ice_breaker_generation"
            )

            result = json.loads(response)
            return result['ice_breakers']

        except Exception as e:
            print(f"AI ice breaker error: {str(e)}")
            # Fallback ice breakers
            if shared_interests:
                interest = list(shared_interests)[0]
                return [
                    f"Hey {profile2.name}! I noticed we both love {interest}. What got you into it?",
                    f"Hi! I see you're into {interest} too. Have any recommendations?",
                    f"Hey! Fellow {interest} enthusiast here. What's your favorite thing about it?"
                ]
            else:
                return [
                    f"Hey {profile2.name}! Your profile caught my attention. How's your week going?",
                    f"Hi {profile2.name}! I'd love to get to know you better. What do you like to do for fun?",
                    f"Hey! I thought we might click. Tell me something interesting about yourself!"
                ]

    # ========================================================================
    # Content Moderation
    # ========================================================================

    async def moderate_content(
        self,
        content: str,
        content_type: str = "message"
    ) -> Tuple[float, bool]:
        """
        Moderate content for safety

        Returns:
            Tuple of (safety_score, is_safe)
        """
        try:
            # Use OpenAI Moderation API
            response = openai.Moderation.create(input=content)

            result = response["results"][0]

            # Calculate safety score (inverse of highest category score)
            max_score = max(result["category_scores"].values())
            safety_score = (1 - max_score) * 100

            is_safe = not result["flagged"]

            return safety_score, is_safe

        except Exception as e:
            print(f"Moderation error: {str(e)}")
            # Default to safe if moderation fails
            return 95.0, True

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def _call_openai(
        self,
        prompt: str,
        system_message: str,
        user_id: Optional[int],
        operation: str
    ) -> str:
        """Call OpenAI API and log the request"""

        start_time = datetime.utcnow()

        try:
            response = openai.ChatCompletion.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                response_format={"type": "json_object"}  # Force JSON response
            )

            # Extract response
            content = response.choices[0].message.content
            usage = response.usage

            # Log AI call
            self._log_ai_call(
                user_id=user_id,
                operation=operation,
                model=GPT_MODEL,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
                success=True
            )

            return content

        except Exception as e:
            # Log error
            self._log_ai_call(
                user_id=user_id,
                operation=operation,
                model=GPT_MODEL,
                success=False,
                error_message=str(e)
            )
            raise

    def _log_ai_call(
        self,
        user_id: Optional[int],
        operation: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Log AI API call for monitoring"""

        # Calculate cost (actual OpenAI pricing)
        cost = 0.0
        if model == "gpt-5-nano":
            cost = (prompt_tokens * 0.05 + completion_tokens * 0.40) / 1_000_000
        elif model == "gpt-4":
            cost = (prompt_tokens * 0.03 + completion_tokens * 0.06) / 1000
        elif model == "gpt-3.5-turbo":
            cost = (prompt_tokens * 0.0015 + completion_tokens * 0.002) / 1000

        log = AILog(
            user_id=user_id,
            operation=operation,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
            success=success,
            error_message=error_message
        )

        self.db.add(log)
        self.db.commit()

    def _parse_compatibility_response(self, response: str) -> Dict:
        """Parse AI compatibility response"""
        result = json.loads(response)

        # Validate and normalize
        score = max(0, min(100, result.get('score', 50)))
        reasons = result.get('reasons', [])[:3]  # Max 3 reasons
        ice_breakers = result.get('ice_breakers', [])[:3]  # Max 3 ice breakers

        return {
            'score': score,
            'reasons': reasons,
            'ice_breakers': ice_breakers
        }

    def _fallback_compatibility(
        self,
        profile1: Profile,
        profile2: Profile
    ) -> Tuple[float, List[str], List[str]]:
        """Simple fallback compatibility algorithm"""

        score = 50.0
        reasons = []

        # Check shared interests
        interests1 = set(i.name for i in profile1.interests) if profile1.interests else set()
        interests2 = set(i.name for i in profile2.interests) if profile2.interests else set()
        shared = interests1 & interests2

        if shared:
            score += len(shared) * 10
            reasons.append(f"You both enjoy {', '.join(list(shared)[:2])}")

        # Age compatibility
        age1 = self._calculate_age(profile1.date_of_birth)
        age2 = self._calculate_age(profile2.date_of_birth)
        age_diff = abs(age1 - age2)

        if age_diff <= 5:
            score += 10
            reasons.append("You're in a similar life stage")

        # Location
        if profile1.location and profile2.location:
            if profile1.location.lower() == profile2.location.lower():
                score += 15
                reasons.append("You're both in the same area")

        score = min(score, 100)

        # Generic ice breakers
        ice_breakers = [
            f"Hey {profile2.name}! How's it going?",
            "Hi! I'd love to get to know you better.",
            "Hey! Your profile caught my eye. What do you like to do for fun?"
        ]

        return score, reasons, ice_breakers

    @staticmethod
    def _calculate_age(date_of_birth: datetime) -> int:
        """Calculate age from date of birth"""
        today = datetime.now()
        age = today.year - date_of_birth.year
        if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
            age -= 1
        return age
