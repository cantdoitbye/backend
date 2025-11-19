# 🚀 Postman Testing Guide - Vibe to Content Mutations

**✨ Updated with Dropdown Enum Support!**

This guide provides ready-to-use GraphQL mutation queries for testing the new vibe sending features in Postman.

---

## 📋 Prerequisites

Before testing, ensure you have:
- Valid user authentication token
- UID of the content you want to send vibe to
- IndividualVibe ID (from vibe_manager_individualvibe table)
- Postman collection with GraphQL endpoint configured

---

## 🆕 Using Dropdowns (Enum Types)

Both mutations now use **Enum types** for `contentCategory`:
- ✅ Use **UPPERCASE without quotes**: `ACHIEVEMENT`, `EDUCATION`, etc.
- ✅ GraphQL Playground will show **dropdown** with all options
- ✅ **Automatic validation** - can't send invalid categories
- ✅ Better developer experience with autocomplete

**Format:** `contentCategory: ACHIEVEMENT` (not `"achievement"`)

---

## 🎯 Mutation 1: Send Vibe to Profile Content

### Content Category Options (Dropdown)
- `ACHIEVEMENT` - User achievements and accomplishments
- `EDUCATION` - Educational background and qualifications
- `SKILL` - User skills and competencies
- `EXPERIENCE` - Professional work experience

### Example 1.1: Send Vibe to Achievement

**GraphQL Query:**
```graphql
mutation {
  sendVibeToProfileContent(input: {
    contentUid: "YOUR_ACHIEVEMENT_UID"
    contentCategory: ACHIEVEMENT
    individualVibeId: 1
    vibeIntensity: 4.5
  }) {
    success
    message
    profileContentVibe {
      uid
      vibeName
      vibeIntensity
      timestamp
      reactedBy {
        uid
        username
        fullName
      }
    }
  }
}
```

**Postman Body (raw JSON):**
```json
{
  "query": "mutation { sendVibeToProfileContent(input: { contentUid: \"YOUR_ACHIEVEMENT_UID\", contentCategory: ACHIEVEMENT, individualVibeId: 1, vibeIntensity: 4.5 }) { success message profileContentVibe { uid vibeName vibeIntensity timestamp reactedBy { uid username fullName } } } }"
}
```

**Note:** Use `ACHIEVEMENT` (no quotes) in the GraphQL string.

---

### Example 1.2: Send Vibe to Education

**GraphQL Query:**
```graphql
mutation {
  sendVibeToProfileContent(input: {
    contentUid: "YOUR_EDUCATION_UID"
    contentCategory: EDUCATION
    individualVibeId: 2
    vibeIntensity: 3.8
  }) {
    success
    message
    profileContentVibe {
      uid
      vibeName
      vibeIntensity
    }
  }
}
```

**Postman Body (raw JSON):**
```json
{
  "query": "mutation { sendVibeToProfileContent(input: { contentUid: \"YOUR_EDUCATION_UID\", contentCategory: EDUCATION, individualVibeId: 2, vibeIntensity: 3.8 }) { success message profileContentVibe { uid vibeName vibeIntensity } } }"
}
```

---

### Example 1.3: Send Vibe to Skill

**GraphQL Query:**
```graphql
mutation {
  sendVibeToProfileContent(input: {
    contentUid: "YOUR_SKILL_UID"
    contentCategory: SKILL
    individualVibeId: 3
    vibeIntensity: 5.0
  }) {
    success
    message
    profileContentVibe {
      uid
      vibeName
      vibeIntensity
    }
  }
}
```

**Postman Body (raw JSON):**
```json
{
  "query": "mutation { sendVibeToProfileContent(input: { contentUid: \"YOUR_SKILL_UID\", contentCategory: SKILL, individualVibeId: 3, vibeIntensity: 5.0 }) { success message profileContentVibe { uid vibeName vibeIntensity } } }"
}
```

---

### Example 1.4: Send Vibe to Experience

**GraphQL Query:**
```graphql
mutation {
  sendVibeToProfileContent(input: {
    contentUid: "YOUR_EXPERIENCE_UID"
    contentCategory: EXPERIENCE
    individualVibeId: 1
    vibeIntensity: 4.2
  }) {
    success
    message
    profileContentVibe {
      uid
      vibeName
      vibeIntensity
    }
  }
}
```

**Postman Body (raw JSON):**
```json
{
  "query": "mutation { sendVibeToProfileContent(input: { contentUid: \"YOUR_EXPERIENCE_UID\", contentCategory: EXPERIENCE, individualVibeId: 1, vibeIntensity: 4.2 }) { success message profileContentVibe { uid vibeName vibeIntensity } } }"
}
```

---

## 🎯 Mutation 2: Send Vibe to Community Content

### Content Category Options (Dropdown)
- `ACHIEVEMENT` - Community achievements and milestones
- `ACTIVITY` - Community activities and events
- `GOAL` - Community goals and objectives
- `AFFILIATION` - Community affiliations and partnerships

### Example 2.1: Send Vibe to Community Achievement

**GraphQL Query:**
```graphql
mutation {
  sendVibeToCommunityContent(input: {
    contentUid: "YOUR_COMMUNITY_ACHIEVEMENT_UID"
    contentCategory: ACHIEVEMENT
    individualVibeId: 1
    vibeIntensity: 4.8
  }) {
    success
    message
    communityContentVibe {
      uid
      vibeName
      vibeIntensity
      timestamp
      reactedBy {
        uid
        username
        fullName
      }
    }
  }
}
```

**Postman Body (raw JSON):**
```json
{
  "query": "mutation { sendVibeToCommunityContent(input: { contentUid: \"YOUR_COMMUNITY_ACHIEVEMENT_UID\", contentCategory: ACHIEVEMENT, individualVibeId: 1, vibeIntensity: 4.8 }) { success message communityContentVibe { uid vibeName vibeIntensity timestamp reactedBy { uid username fullName } } } }"
}
```

**Note:** For community content, use `ACHIEVEMENT` (not `community_achievement`). The enum value handles the mapping internally.

---

### Example 2.2: Send Vibe to Community Activity

**GraphQL Query:**
```graphql
mutation {
  sendVibeToCommunityContent(input: {
    contentUid: "YOUR_COMMUNITY_ACTIVITY_UID"
    contentCategory: ACTIVITY
    individualVibeId: 2
    vibeIntensity: 5.0
  }) {
    success
    message
    communityContentVibe {
      uid
      vibeName
      vibeIntensity
    }
  }
}
```

**Postman Body (raw JSON):**
```json
{
  "query": "mutation { sendVibeToCommunityContent(input: { contentUid: \"YOUR_COMMUNITY_ACTIVITY_UID\", contentCategory: ACTIVITY, individualVibeId: 2, vibeIntensity: 5.0 }) { success message communityContentVibe { uid vibeName vibeIntensity } } }"
}
```

---

### Example 2.3: Send Vibe to Community Goal

**GraphQL Query:**
```graphql
mutation {
  sendVibeToCommunityContent(input: {
    contentUid: "YOUR_COMMUNITY_GOAL_UID"
    contentCategory: GOAL
    individualVibeId: 3
    vibeIntensity: 4.5
  }) {
    success
    message
    communityContentVibe {
      uid
      vibeName
      vibeIntensity
    }
  }
}
```

**Postman Body (raw JSON):**
```json
{
  "query": "mutation { sendVibeToCommunityContent(input: { contentUid: \"YOUR_COMMUNITY_GOAL_UID\", contentCategory: GOAL, individualVibeId: 3, vibeIntensity: 4.5 }) { success message communityContentVibe { uid vibeName vibeIntensity } } }"
}
```

---

### Example 2.4: Send Vibe to Community Affiliation

**GraphQL Query:**
```graphql
mutation {
  sendVibeToCommunityContent(input: {
    contentUid: "YOUR_COMMUNITY_AFFILIATION_UID"
    contentCategory: AFFILIATION
    individualVibeId: 1
    vibeIntensity: 4.0
  }) {
    success
    message
    communityContentVibe {
      uid
      vibeName
      vibeIntensity
    }
  }
}
```

**Postman Body (raw JSON):**
```json
{
  "query": "mutation { sendVibeToCommunityContent(input: { contentUid: \"YOUR_COMMUNITY_AFFILIATION_UID\", contentCategory: AFFILIATION, individualVibeId: 1, vibeIntensity: 4.0 }) { success message communityContentVibe { uid vibeName vibeIntensity } } }"
}
```

---

## 📌 Important Notes

### Enum Values (IMPORTANT!)

**Profile Content:**
- ✅ `ACHIEVEMENT` (not `"achievement"`)
- ✅ `EDUCATION` (not `"education"`)
- ✅ `SKILL` (not `"skill"`)
- ✅ `EXPERIENCE` (not `"experience"`)

**Community Content:**
- ✅ `ACHIEVEMENT` (not `"community_achievement"`)
- ✅ `ACTIVITY` (not `"community_activity"`)
- ✅ `GOAL` (not `"community_goal"`)
- ✅ `AFFILIATION` (not `"community_affiliation"`)

The enum handles the internal mapping automatically!

### Field Descriptions

**contentUid**: UID of the content item (achievement, education, skill, experience, community item)
**contentCategory**: Category from dropdown (enum)
**individualVibeId**: ID from `vibe_manager_individualvibe` table
**vibeIntensity**: Float between 1.0 and 5.0

---

## 🧪 Testing Workflow

### Step 1: Get Content UID
Query for the content you want to vibe:
```graphql
query {
  achievementByUid(uid: "YOUR_UID") {
    uid
    title
    description
  }
}
```

### Step 2: Get Individual Vibe IDs
Query available vibes:
```graphql
query {
  getAllVibes {
    id
    nameOfVibe
    weightageIaq
    weightageIiq
    weightageIhq
    weightageIsq
  }
}
```

### Step 3: Send Vibe
Use one of the mutations above with:
- Content UID from Step 1
- Vibe ID from Step 2
- Appropriate category from dropdown
- Intensity (1.0 to 5.0)

### Step 4: Verify
Query the content again to see the vibe:
```graphql
query {
  achievementByUid(uid: "YOUR_UID") {
    uid
    title
    vibesCount
    myVibeDetails {
      vibeName
      vibeIntensity
    }
  }
}
```

---

## ⚠️ Expected Responses

### Success Response
```json
{
  "data": {
    "sendVibeToProfileContent": {
      "success": true,
      "message": "Vibe sent successfully to achievement",
      "profileContentVibe": {
        "uid": "pcv_abc123",
        "vibeName": "Inspiring",
        "vibeIntensity": 4.5,
        "timestamp": "2024-01-15T10:30:00",
        "reactedBy": {
          "uid": "user_xyz",
          "username": "john_doe",
          "fullName": "John Doe"
        }
      }
    }
  }
}
```

### Error Responses

**Invalid Content UID:**
```json
{
  "errors": [{
    "message": "Achievement with UID YOUR_ACHIEVEMENT_UID not found"
  }]
}
```

**Invalid Vibe ID:**
```json
{
  "errors": [{
    "message": "IndividualVibe with id 999 not found"
  }]
}
```

**Invalid Category (if using string instead of enum):**
```json
{
  "errors": [{
    "message": "Argument 'contentCategory' has invalid value. Expected type 'ProfileContentCategoryEnum'."
  }]
}
```

**Invalid Intensity:**
```json
{
  "errors": [{
    "message": "Vibe intensity must be between 1.0 and 5.0"
  }]
}
```

**Not Community Member (for community content):**
```json
{
  "errors": [{
    "message": "User is not a member of the community"
  }]
}
```

---

## 🎨 GraphQL Playground Features

When using GraphQL Playground (not Postman):

1. **Autocomplete**: Type `contentCategory:` and press `Ctrl+Space`
   - See dropdown with: `ACHIEVEMENT`, `EDUCATION`, `SKILL`, `EXPERIENCE`

2. **Documentation**: Hover over `contentCategory`
   - See descriptions for each option

3. **Validation**: Try typing wrong value
   - Get instant error with valid options

4. **Schema Explorer**: Browse available enums
   - See `ProfileContentCategoryEnum`
   - See `CommunityContentCategoryEnum`

---

## 🔗 Quick Reference

### Profile Content Enum Values
```graphql
enum ProfileContentCategoryEnum {
  ACHIEVEMENT  # User achievements and accomplishments
  EDUCATION    # Educational background and qualifications
  SKILL        # User skills and competencies
  EXPERIENCE   # Professional work experience
}
```

### Community Content Enum Values
```graphql
enum CommunityContentCategoryEnum {
  ACHIEVEMENT  # Community achievements and milestones (maps to community_achievement)
  ACTIVITY     # Community activities and events (maps to community_activity)
  GOAL         # Community goals and objectives (maps to community_goal)
  AFFILIATION  # Community affiliations and partnerships (maps to community_affiliation)
}
```

---

## ✅ Testing Checklist

- [ ] Test sending vibe to achievement
- [ ] Test sending vibe to education
- [ ] Test sending vibe to skill
- [ ] Test sending vibe to experience
- [ ] Test sending vibe to community achievement
- [ ] Test sending vibe to community activity
- [ ] Test sending vibe to community goal
- [ ] Test sending vibe to community affiliation
- [ ] Test updating existing vibe (send vibe twice to same content)
- [ ] Test with different vibe intensities (1.0, 2.5, 5.0)
- [ ] Test with different individual vibe IDs
- [ ] Verify vibe counts increase correctly
- [ ] Verify myVibeDetails returns correct data
- [ ] Test error cases (invalid UID, invalid vibe ID, etc.)

---

## 🚀 Next Steps

After successful testing:
1. Verify user scores are updated correctly (`VibeUtils.onVibeCreated`)
2. Check vibe activity tracking in database
3. Verify vibes appear in content queries
4. Test with multiple users
5. Performance test with multiple concurrent vibes

---

**Happy Testing!** 🎉

For any issues or questions, refer to:
- `VIBE_TO_CONTENT_IMPLEMENTATION_SUMMARY.md` - Full implementation details
- `CYPHER_QUERY_SAFETY_ANALYSIS.md` - Query safety analysis
- `ENUM_DROPDOWN_UPDATE.md` - Enum dropdown features


