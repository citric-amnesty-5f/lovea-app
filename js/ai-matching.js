// AI Matching Engine with ChatGPT Integration
class AIMatchingEngine {
    constructor() {
        this.apiKey = null;
        this.apiEndpoint = 'https://api.openai.com/v1/chat/completions';
        this.model = 'gpt-4';
    }

    setApiKey(key) {
        this.apiKey = key;
        localStorage.setItem('openai_api_key', key);
        console.log('OpenAI API key set successfully');
    }

    getApiKey() {
        if (!this.apiKey) {
            this.apiKey = localStorage.getItem('openai_api_key');
        }
        return this.apiKey;
    }

    hasApiKey() {
        return !!this.getApiKey();
    }

    async callChatGPT(messages, temperature = 0.7) {
        const apiKey = this.getApiKey();
        if (!apiKey) {
            throw new Error('OpenAI API key not set. Please configure it in settings.');
        }

        try {
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiKey}`
                },
                body: JSON.stringify({
                    model: this.model,
                    messages: messages,
                    temperature: temperature,
                    max_tokens: 500
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error?.message || 'API request failed');
            }

            const data = await response.json();
            return data.choices[0].message.content;
        } catch (error) {
            console.error('ChatGPT API Error:', error);
            throw error;
        }
    }

    // Generate AI compatibility score between two profiles
    async calculateCompatibility(profile1, profile2) {
        if (!this.hasApiKey()) {
            // Fallback to simple algorithm if no API key
            return this.calculateSimpleCompatibility(profile1, profile2);
        }

        try {
            const prompt = `Analyze the compatibility between these two dating profiles and provide a compatibility score from 0-100.

Profile 1:
Name: ${profile1.name}
Age: ${profile1.age}
Occupation: ${profile1.occupation || 'Not specified'}
Bio: ${profile1.bio || 'No bio'}
Interests: ${profile1.interests?.join(', ') || 'Not specified'}
Location: ${profile1.location || 'Not specified'}

Profile 2:
Name: ${profile2.name}
Age: ${profile2.age}
Occupation: ${profile2.occupation || 'Not specified'}
Bio: ${profile2.bio || 'No bio'}
Interests: ${profile2.interests?.join(', ') || 'Not specified'}
Location: ${profile2.location || 'Not specified'}

Respond ONLY with a JSON object in this format:
{
  "score": <number 0-100>,
  "reason": "<brief explanation of the score>",
  "highlights": ["<positive aspect 1>", "<positive aspect 2>"],
  "concerns": ["<potential concern 1>", "<potential concern 2>"]
}`;

            const messages = [
                {
                    role: 'system',
                    content: 'You are an expert relationship compatibility analyzer. Analyze profiles based on shared interests, compatible lifestyles, age compatibility, location proximity, and personality indicators from bios. Be realistic and nuanced in your analysis.'
                },
                {
                    role: 'user',
                    content: prompt
                }
            ];

            const response = await this.callChatGPT(messages, 0.5);

            // Parse JSON response
            const jsonMatch = response.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                const result = JSON.parse(jsonMatch[0]);
                return {
                    score: Math.min(100, Math.max(0, result.score)),
                    reason: result.reason,
                    highlights: result.highlights || [],
                    concerns: result.concerns || []
                };
            } else {
                throw new Error('Invalid response format');
            }
        } catch (error) {
            console.error('AI compatibility calculation failed, using fallback:', error);
            return this.calculateSimpleCompatibility(profile1, profile2);
        }
    }

    // Fallback compatibility algorithm (no API needed)
    calculateSimpleCompatibility(profile1, profile2) {
        let score = 50; // Base score

        // Age compatibility (within 10 years = good)
        const ageDiff = Math.abs(profile1.age - profile2.age);
        if (ageDiff <= 5) score += 15;
        else if (ageDiff <= 10) score += 10;
        else if (ageDiff <= 15) score += 5;
        else score -= 10;

        // Location compatibility
        if (profile1.location && profile2.location) {
            const loc1 = profile1.location.toLowerCase();
            const loc2 = profile2.location.toLowerCase();
            if (loc1.includes('ny') && loc2.includes('ny')) score += 15;
            else if (loc1.split(',')[1]?.trim() === loc2.split(',')[1]?.trim()) score += 10;
        }

        // Interest compatibility
        if (profile1.interests && profile2.interests &&
            profile1.interests.length > 0 && profile2.interests.length > 0) {
            const commonInterests = profile1.interests.filter(i =>
                profile2.interests.some(j => j.toLowerCase() === i.toLowerCase())
            );
            score += Math.min(20, commonInterests.length * 5);
        }

        // Bio keyword matching (simple similarity)
        if (profile1.bio && profile2.bio) {
            const keywords = ['travel', 'music', 'food', 'fitness', 'art', 'reading', 'movies', 'hiking', 'cooking'];
            let bioMatches = 0;
            keywords.forEach(keyword => {
                if (profile1.bio.toLowerCase().includes(keyword) &&
                    profile2.bio.toLowerCase().includes(keyword)) {
                    bioMatches++;
                }
            });
            score += Math.min(10, bioMatches * 2);
        }

        // Random variation for realism
        score += Math.random() * 10 - 5;

        return {
            score: Math.min(100, Math.max(0, Math.round(score))),
            reason: 'Compatibility based on age, location, and profile details',
            highlights: ['Good age compatibility', 'Similar location'],
            concerns: ageDiff > 15 ? ['Significant age difference'] : []
        };
    }

    // Generate personalized conversation starters
    async generateConversationStarters(userProfile, matchProfile) {
        if (!this.hasApiKey()) {
            return this.getGenericConversationStarters();
        }

        try {
            const prompt = `Generate 3 personalized conversation starters for ${userProfile.name} to use when chatting with ${matchProfile.name}.

${userProfile.name}'s Profile:
Bio: ${userProfile.bio || 'No bio'}
Interests: ${userProfile.interests?.join(', ') || 'Not specified'}

${matchProfile.name}'s Profile:
Bio: ${matchProfile.bio || 'No bio'}
Interests: ${matchProfile.interests?.join(', ') || 'Not specified'}
Occupation: ${matchProfile.occupation || 'Not specified'}

Create engaging, specific starters based on their profiles. Make them natural and friendly.
Respond with only a JSON array of 3 strings.`;

            const messages = [
                {
                    role: 'system',
                    content: 'You are a dating conversation expert. Create personalized, engaging conversation starters that reference specific details from profiles.'
                },
                {
                    role: 'user',
                    content: prompt
                }
            ];

            const response = await this.callChatGPT(messages, 0.8);
            const jsonMatch = response.match(/\[[\s\S]*\]/);

            if (jsonMatch) {
                return JSON.parse(jsonMatch[0]);
            } else {
                return this.getGenericConversationStarters();
            }
        } catch (error) {
            console.error('Failed to generate conversation starters:', error);
            return this.getGenericConversationStarters();
        }
    }

    getGenericConversationStarters() {
        return [
            "Hey! I saw we both like similar things. What's been keeping you busy lately?",
            "Hi! Your profile caught my eye. Tell me more about yourself!",
            "Hey there! How's your day going?"
        ];
    }

    // Generate profile bio suggestions
    async generateBioSuggestions(userInfo) {
        if (!this.hasApiKey()) {
            return this.getGenericBioSuggestions();
        }

        try {
            const prompt = `Create 3 dating profile bio suggestions for:
Name: ${userInfo.name}
Age: ${userInfo.age}
Occupation: ${userInfo.occupation || 'Not specified'}
Interests: ${userInfo.interests?.join(', ') || 'Not specified'}

Make them engaging, authentic, and 2-3 sentences each. Show personality.
Respond with only a JSON array of 3 strings.`;

            const messages = [
                {
                    role: 'system',
                    content: 'You are a dating profile expert. Write engaging, authentic bios that showcase personality and interests without being cliché.'
                },
                {
                    role: 'user',
                    content: prompt
                }
            ];

            const response = await this.callChatGPT(messages, 0.9);
            const jsonMatch = response.match(/\[[\s\S]*\]/);

            if (jsonMatch) {
                return JSON.parse(jsonMatch[0]);
            } else {
                return this.getGenericBioSuggestions();
            }
        } catch (error) {
            console.error('Failed to generate bio suggestions:', error);
            return this.getGenericBioSuggestions();
        }
    }

    getGenericBioSuggestions() {
        return [
            "I love exploring new places and trying new foods. Always up for an adventure! Let's grab coffee and see where it goes.",
            "Passionate about my work and my hobbies. Looking for someone to share new experiences with.",
            "Life's too short to be boring! I enjoy good conversations, great food, and even better company."
        ];
    }

    // Analyze user's dating patterns
    async analyzeUserPatterns(user, interactions, matches) {
        if (!this.hasApiKey()) {
            return this.getSimplePatternAnalysis(interactions, matches);
        }

        try {
            const likeCount = interactions.filter(i => i.type === 'like').length;
            const passCount = interactions.filter(i => i.type === 'pass').length;
            const matchCount = matches.length;

            const prompt = `Analyze this user's dating app behavior and provide insights:

Stats:
- Profiles Liked: ${likeCount}
- Profiles Passed: ${passCount}
- Matches: ${matchCount}
- Success Rate: ${likeCount > 0 ? (matchCount / likeCount * 100).toFixed(1) : 0}%

Provide 3-5 personalized insights or tips to improve their dating experience.
Respond with only a JSON array of strings.`;

            const messages = [
                {
                    role: 'system',
                    content: 'You are a dating coach providing helpful, encouraging insights based on user behavior.'
                },
                {
                    role: 'user',
                    content: prompt
                }
            ];

            const response = await this.callChatGPT(messages, 0.7);
            const jsonMatch = response.match(/\[[\s\S]*\]/);

            if (jsonMatch) {
                return JSON.parse(jsonMatch[0]);
            } else {
                return this.getSimplePatternAnalysis(interactions, matches);
            }
        } catch (error) {
            console.error('Failed to analyze patterns:', error);
            return this.getSimplePatternAnalysis(interactions, matches);
        }
    }

    getSimplePatternAnalysis(interactions, matches) {
        const likeCount = interactions.filter(i => i.type === 'like').length;
        const passCount = interactions.filter(i => i.type === 'pass').length;
        const insights = [];

        if (likeCount > passCount * 2) {
            insights.push("You're quite open to connections! Consider being more selective to improve match quality.");
        } else if (passCount > likeCount * 2) {
            insights.push("You have high standards! That's great, but try being open to unexpected connections.");
        }

        if (matches.length > 0) {
            insights.push(`You have ${matches.length} match${matches.length > 1 ? 'es' : ''}! Don't forget to start conversations.`);
        }

        if (likeCount < 5) {
            insights.push("Keep exploring profiles to find great matches!");
        }

        insights.push("Complete your profile with photos and interests to attract better matches.");

        return insights;
    }
}

// Global AI engine instance
const aiEngine = new AIMatchingEngine();
