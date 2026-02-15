// Onboarding Flow for New Users

let onboardingStep = 0;
let selectedInterests = []; // Persistent storage for selected interests
let customInterests = [];   // Persistent storage for custom interests

async function startOnboarding() {
    // Check if user has completed onboarding
    // Use currentUser.profile which is already loaded from backend
    if (currentUser && currentUser.profile && currentUser.profile.onboarding_completed) {
        // Skip onboarding
        return;
    }

    // Reset onboarding state
    onboardingStep = 0;
    selectedInterests = [];  // Clear previous selections
    customInterests = [];    // Clear previous custom interests

    showOnboardingModal();
}

function showOnboardingModal() {
    const modal = document.createElement('div');
    modal.className = 'onboarding-modal active';
    modal.id = 'onboardingModal';

    modal.innerHTML = `
        <div class="onboarding-content">
            <div class="onboarding-progress">
                <div class="progress-bar">
                    <div class="progress-fill" id="onboardingProgress" style="width: 0%"></div>
                </div>
                <div class="progress-text"><span id="currentStep">1</span> of 5</div>
            </div>
            <div class="onboarding-step" id="onboardingStepContent"></div>
        </div>
    `;

    document.body.appendChild(modal);
    showOnboardingStep(0);
}

function showOnboardingStep(step) {
    onboardingStep = step;

    const content = document.getElementById('onboardingStepContent');
    const progress = document.getElementById('onboardingProgress');
    const stepNumber = document.getElementById('currentStep');

    if (!content) return;

    stepNumber.textContent = step + 1;
    progress.style.width = ((step + 1) / 5 * 100) + '%';

    switch (step) {
        case 0:
            content.innerHTML = getWelcomeStep();
            break;
        case 1:
            content.innerHTML = getProfilePhotoStep();
            break;
        case 2:
            content.innerHTML = getAboutYouStep();
            break;
        case 3:
            content.innerHTML = getInterestsStep();
            // Restore selected state from persistent storage
            setTimeout(() => {
                selectedInterests.forEach(interest => {
                    const pill = document.querySelector(`.interest-pill[data-interest="${interest}"]`);
                    if (pill) {
                        pill.classList.add('selected');
                    }
                });
                // Restore custom interests
                customInterests.forEach(interest => {
                    addCustomInterest(interest, true);
                });
            }, 0);
            break;
        case 4:
            content.innerHTML = getPreferencesStep();
            break;
    }
}

function getWelcomeStep() {
    return `
        <div class="onboarding-step-content">
            <div class="onboarding-icon">👋</div>
            <h2>Welcome to LoveAI!</h2>
            <p>Let's set up your profile in just a few steps.</p>
            <p>Our AI will help you find amazing matches based on compatibility.</p>
            <div class="onboarding-actions">
                <button class="btn btn-primary btn-large" onclick="nextOnboardingStep()">Get Started</button>
            </div>
        </div>
    `;
}

function getProfilePhotoStep() {
    return `
        <div class="onboarding-step-content">
            <div class="onboarding-icon">📸</div>
            <h2>Add Your Photos</h2>
            <p>Choose an avatar emoji or upload photos</p>

            <div class="form-group">
                <label>Avatar Emoji</label>
                <input type="text" id="onboardingAvatar" maxlength="2"
                       placeholder="👤" value="👤">
            </div>

            <div class="form-group">
                <label>Upload Photos (optional)</label>
                <input type="file" id="onboardingPhotos" accept="image/*" multiple>
                <small>You can add up to 6 photos</small>
            </div>

            <div class="onboarding-actions">
                <button class="btn btn-secondary" onclick="previousOnboardingStep()">Back</button>
                <button class="btn btn-primary" onclick="nextOnboardingStep()">Next</button>
            </div>
        </div>
    `;
}

function getAboutYouStep() {
    return `
        <div class="onboarding-step-content">
            <div class="onboarding-icon">✍️</div>
            <h2>About You</h2>
            <p>Tell others a bit about yourself</p>

            <div class="form-group">
                <label>Your Bio</label>
                <textarea id="onboardingBio" rows="4"
                          placeholder="I love hiking, trying new restaurants, and..."></textarea>
                ${aiEngine.hasApiKey() ?
            '<button class="btn btn-sm" onclick="generateOnboardingBio()">✨ AI Suggestions</button>' : ''}
            </div>

            <div class="form-group">
                <label>Occupation</label>
                <input type="text" id="onboardingOccupation"
                       placeholder="Software Engineer, Teacher, etc.">
            </div>

            <div class="form-group">
                <label>Location</label>
                <input type="text" id="onboardingLocation"
                       placeholder="New York, NY">
            </div>

            <div class="onboarding-actions">
                <button class="btn btn-secondary" onclick="previousOnboardingStep()">Back</button>
                <button class="btn btn-primary" onclick="nextOnboardingStep()">Next</button>
            </div>
        </div>
    `;
}

function getInterestsStep() {
    const commonInterests = [
        'Travel', 'Food', 'Fitness', 'Music', 'Movies', 'Reading',
        'Hiking', 'Cooking', 'Art', 'Photography', 'Gaming', 'Yoga',
        'Dancing', 'Coffee', 'Wine', 'Sports', 'Pets', 'Fashion'
    ];

    return `
        <div class="onboarding-step-content">
            <div class="onboarding-icon">❤️</div>
            <h2>Your Interests</h2>
            <p>Select at least 3 interests</p>

            <div class="interests-selector">
                ${commonInterests.map(interest => `
                    <button class="interest-pill" onclick="toggleInterest(this)" data-interest="${interest}">
                        ${interest}
                    </button>
                `).join('')}
            </div>

            <div class="form-group">
                <label>Add custom interest</label>
                <input type="text" id="customInterest" placeholder="Type and press Enter">
            </div>

            <div class="onboarding-actions">
                <button class="btn btn-secondary" onclick="previousOnboardingStep()">Back</button>
                <button class="btn btn-primary" onclick="nextOnboardingStep()">Next</button>
            </div>
        </div>
    `;
}

function getPreferencesStep() {
    return `
        <div class="onboarding-step-content">
            <div class="onboarding-icon">🎯</div>
            <h2>Your Preferences</h2>
            <p>Who would you like to meet?</p>

            <div class="form-group">
                <label>Age Range</label>
                <div class="range-inputs">
                    <input type="number" id="prefAgeMin" value="25" min="18" max="100">
                    <span>to</span>
                    <input type="number" id="prefAgeMax" value="35" min="18" max="100">
                </div>
            </div>

            <div class="form-group">
                <label>Show Me</label>
                <select id="prefGender">
                    <option value="all">Everyone</option>
                    <option value="M">Men</option>
                    <option value="F">Women</option>
                    <option value="T">Non-binary</option>
                </select>
            </div>

            <div class="form-group">
                <label>Distance (miles)</label>
                <input type="range" id="prefDistance" value="25" min="1" max="100"
                       oninput="this.nextElementSibling.textContent = this.value + ' miles'">
                <span>25 miles</span>
            </div>

            <div class="onboarding-actions">
                <button class="btn btn-secondary" onclick="previousOnboardingStep()">Back</button>
                <button class="btn btn-primary btn-large" onclick="completeOnboarding()">
                    Complete Setup 🎉
                </button>
            </div>
        </div>
    `;
}

function nextOnboardingStep() {
    if (onboardingStep < 4) {
        showOnboardingStep(onboardingStep + 1);
    }
}

function previousOnboardingStep() {
    if (onboardingStep > 0) {
        showOnboardingStep(onboardingStep - 1);
    }
}

function toggleInterest(button) {
    const interest = button.dataset.interest;
    button.classList.toggle('selected');

    // Update persistent state
    if (button.classList.contains('selected')) {
        if (!selectedInterests.includes(interest)) {
            selectedInterests.push(interest);
        }
    } else {
        selectedInterests = selectedInterests.filter(i => i !== interest);
    }
}

async function generateOnboardingBio() {
    try {
        showStatus('Generating bio suggestions...');

        const userInfo = {
            name: currentUser.name,
            age: currentUser.age,
            occupation: document.getElementById('onboardingOccupation')?.value || '',
            interests: getSelectedInterests()
        };

        const suggestions = await aiEngine.generateBioSuggestions(userInfo);

        const suggestionsDiv = document.createElement('div');
        suggestionsDiv.className = 'bio-suggestions';
        suggestionsDiv.innerHTML = '<h4>Choose a bio:</h4>';

        suggestions.forEach(bio => {
            const btn = document.createElement('button');
            btn.className = 'suggestion-btn';
            btn.textContent = bio;
            btn.onclick = () => {
                document.getElementById('onboardingBio').value = bio;
                suggestionsDiv.remove();
            };
            suggestionsDiv.appendChild(btn);
        });

        document.querySelector('.onboarding-step-content').appendChild(suggestionsDiv);
        showStatus('');
    } catch (error) {
        showStatus('Failed to generate suggestions');
    }
}

function getSelectedInterests() {
    // Return the persistent state instead of querying DOM
    return [...selectedInterests, ...customInterests];
}

function addCustomInterest(interestText, skipPersist = false) {
    // Validate
    if (!interestText || interestText.trim() === '') return;

    const trimmedInterest = interestText.trim();

    // Check if already exists in either array
    if (selectedInterests.includes(trimmedInterest) || customInterests.includes(trimmedInterest)) {
        return;
    }

    // Add to persistent state
    if (!skipPersist) {
        customInterests.push(trimmedInterest);
    }

    // Create pill element
    const pill = document.createElement('button');
    pill.className = 'interest-pill selected';
    pill.dataset.interest = trimmedInterest;
    pill.innerHTML = `
        ${trimmedInterest}
        <span class="remove-interest" onclick="removeCustomInterest(this, '${trimmedInterest}')">×</span>
    `;
    pill.onclick = function() { toggleInterest(this); };

    const selector = document.querySelector('.interests-selector');
    if (selector) {
        selector.appendChild(pill);
    }
}

function removeCustomInterest(element, interestText) {
    // Remove from persistent state
    customInterests = customInterests.filter(i => i !== interestText);
    selectedInterests = selectedInterests.filter(i => i !== interestText);

    // Remove from DOM
    element.parentElement.remove();
}

async function completeOnboarding() {
    try {
        // Collect all data
        const avatar = document.getElementById('onboardingAvatar')?.value || '👤';
        const bio = document.getElementById('onboardingBio')?.value.trim() || '';
        const occupation = document.getElementById('onboardingOccupation')?.value.trim() || '';
        const location = document.getElementById('onboardingLocation')?.value.trim() || '';
        const interests = getSelectedInterests();

        if (interests.length < 3) {
            showStatus('Please select at least 3 interests');
            return;
        }

        // Prepare profile data for backend API
        const profileData = {
            bio,
            occupation,
            location,
            interests
        };

        // Update profile using backend API
        await window.backendAPI.updateProfile(profileData);

        // Upload photos to backend
        const photos = await handleOnboardingPhotos();
        for (let i = 0; i < photos.length; i++) {
            try {
                await window.backendAPI.uploadPhoto(photos[i].data, photos[i].primary, i);
                console.log(`Onboarding photo ${i + 1} uploaded`);
            } catch (photoErr) {
                console.error(`Onboarding photo ${i + 1} upload failed:`, photoErr);
            }
        }

        // Save preferences
        const genderPref = document.getElementById('prefGender')?.value || 'all';

        // Map gender preference to backend format
        let lookingFor;
        if (genderPref === 'all') {
            lookingFor = ['male', 'female', 'non_binary', 'other'];
        } else if (genderPref === 'M') {
            lookingFor = ['male'];
        } else if (genderPref === 'F') {
            lookingFor = ['female'];
        } else if (genderPref === 'T') {
            lookingFor = ['non_binary'];
        } else {
            lookingFor = ['male', 'female', 'non_binary', 'other'];
        }

        const preferences = {
            min_age: parseInt(document.getElementById('prefAgeMin')?.value || 18),
            max_age: parseInt(document.getElementById('prefAgeMax')?.value || 100),
            max_distance: parseInt(document.getElementById('prefDistance')?.value || 50),
            looking_for: lookingFor
        };

        await window.backendAPI.updatePreferences(preferences);

        // Mark onboarding as complete
        await window.backendAPI.completeOnboarding();

        // Update current user profile
        currentUser.profile = await window.backendAPI.getMyProfile();
        localStorage.setItem('loveai_current_user', JSON.stringify(currentUser));

        // Close onboarding
        document.getElementById('onboardingModal')?.remove();

        // Show success message
        showNotificationToast('Profile created! Start swiping to find matches.', 'success');

        // Navigate to discovery
        showScreen('discover');
    } catch (error) {
        console.error('Error completing onboarding:', error);
        showStatus('Error saving profile');
    }
}

async function handleOnboardingPhotos() {
    const fileInput = document.getElementById('onboardingPhotos');
    if (!fileInput || !fileInput.files.length) return [];

    const photos = [];
    const maxPhotos = Math.min(fileInput.files.length, 6);

    for (let i = 0; i < maxPhotos; i++) {
        const file = fileInput.files[i];

        if (file.size > 5 * 1024 * 1024) {
            showStatus(`Photo ${i + 1} is too large. Max 5MB.`);
            continue;
        }

        const base64 = await fileToBase64(file);
        photos.push({
            id: 'photo_' + Date.now() + '_' + i,
            data: base64,
            primary: i === 0
        });
    }

    return photos;
}

// Setup custom interest input
document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('keypress', (e) => {
        const customInput = document.getElementById('customInterest');
        if (customInput && e.target === customInput && e.key === 'Enter') {
            e.preventDefault();
            const value = customInput.value.trim();
            if (value) {
                addCustomInterest(value);
                customInput.value = '';
            }
        }
    });
});
