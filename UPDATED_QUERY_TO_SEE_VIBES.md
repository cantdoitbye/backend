# Updated Queries to See Vibes in Profile Content

## ✅ Fix Applied

I've updated all profile content types (Achievement, Education, Skill, Experience) to:
1. **Count new vibes** in `vibe_count` field
2. **Return new vibe details** in `vibe_reactions_list` field

---

## 🔍 Updated Query for Achievement with Vibes

### Query to See Your Sent Vibe

```graphql
query {
  achievementByUid(achievementUid: "YOUR_ACHIEVEMENT_UID") {
    uid
    what
    description
    vibeCount
    
    # NEW FIELD: Shows actual ProfileContentVibe nodes
    vibeReactionsList {
      uid
      individualVibeId
      vibeName
      vibeIntensity
      reactedBy {
        uid
        username
        firstName
        lastName
      }
      timestamp
      isActive
    }
    
    # OLD FIELD: Shows aggregated data from reaction manager
    vibeList {
      vibeId
      vibeName
      vibesCount
      vibeCumulativeScore
    }
  }
}
```

### Postman Body (raw JSON)
```json
{
  "query": "query { achievementByUid(achievementUid: \"YOUR_ACHIEVEMENT_UID\") { uid what description vibeCount vibeReactionsList { uid individualVibeId vibeName vibeIntensity reactedBy { uid username firstName lastName } timestamp isActive } vibeList { vibeId vibeName vibesCount vibeCumulativeScore } } }"
}
```

---

## 📊 What Changed

### Before (Old Query)
```graphql
query {
  achievementByUid(achievementUid: "abc123") {
    vibeCount  # Only counted old "like" reactions
    vibeList {  # From reaction manager (may lag behind)
      vibeName
      vibesCount
    }
  }
}
```
**Problem**: Didn't show new `ProfileContentVibe` nodes

### After (New Query) ✅
```graphql
query {
  achievementByUid(achievementUid: "abc123") {
    vibeCount  # NOW counts BOTH old reactions AND new vibes!
    
    vibeReactionsList {  # NEW! Shows actual ProfileContentVibe nodes
      vibeName
      vibeIntensity
      reactedBy {
        username
      }
    }
  }
}
```
**Solution**: Direct access to new vibe nodes!

---

## 🎯 Quick Test Queries

### 1. Minimal Query (Just Check if Vibe Exists)
```graphql
query {
  achievementByUid(achievementUid: "YOUR_UID") {
    vibeCount
    vibeReactionsList {
      vibeName
      vibeIntensity
    }
  }
}
```

**Postman**:
```json
{
  "query": "query { achievementByUid(achievementUid: \"YOUR_UID\") { vibeCount vibeReactionsList { vibeName vibeIntensity } } }"
}
```

---

### 2. Full Details Query
```graphql
query {
  achievementByUid(achievementUid: "YOUR_UID") {
    uid
    what
    vibeCount
    vibeReactionsList {
      uid
      vibeName
      vibeIntensity
      reactedBy {
        username
        firstName
        lastName
      }
      timestamp
    }
  }
}
```

**Postman**:
```json
{
  "query": "query { achievementByUid(achievementUid: \"YOUR_UID\") { uid what vibeCount vibeReactionsList { uid vibeName vibeIntensity reactedBy { username firstName lastName } timestamp } } }"
}
```

---

### 3. Compare Old vs New Vibes
```graphql
query {
  achievementByUid(achievementUid: "YOUR_UID") {
    vibeCount
    
    # Old system (from reaction manager)
    vibeList {
      vibeName
      vibesCount
      vibeCumulativeScore
    }
    
    # New system (actual vibe nodes)
    vibeReactionsList {
      vibeName
      vibeIntensity
      reactedBy {
        username
      }
      timestamp
    }
  }
}
```

---

## 📋 All Profile Content Queries Updated

### Education
```graphql
query {
  educationByUid(educationUid: "YOUR_UID") {
    uid
    what
    vibeCount
    vibeReactionsList {
      vibeName
      vibeIntensity
      reactedBy {
        username
      }
    }
  }
}
```

### Skill
```graphql
query {
  skillByUid(skillUid: "YOUR_UID") {
    uid
    what
    vibeCount
    vibeReactionsList {
      vibeName
      vibeIntensity
      reactedBy {
        username
      }
    }
  }
}
```

### Experience
```graphql
query {
  experienceByUid(experienceUid: "YOUR_UID") {
    uid
    what
    vibeCount
    vibeReactionsList {
      vibeName
      vibeIntensity
      reactedBy {
        username
      }
    }
  }
}
```

---

## 🧪 Testing Workflow

### Step 1: Send a Vibe
```json
{
  "query": "mutation { sendVibeToProfileContent(input: { contentUid: \"YOUR_ACHIEVEMENT_UID\", contentCategory: \"achievement\", individualVibeId: 1, vibeIntensity: 4.5 }) { success message profileContentVibe { vibeName vibeIntensity } } }"
}
```

**Expected Response**:
```json
{
  "data": {
    "sendVibeToProfileContent": {
      "success": true,
      "message": "Vibe sent to profile content successfully!",
      "profileContentVibe": {
        "vibeName": "Inspiring",
        "vibeIntensity": 4.5
      }
    }
  }
}
```

---

### Step 2: Verify Vibe is Visible (NEW FIELD)
```json
{
  "query": "query { achievementByUid(achievementUid: \"YOUR_ACHIEVEMENT_UID\") { vibeCount vibeReactionsList { vibeName vibeIntensity reactedBy { username } timestamp } } }"
}
```

**Expected Response**:
```json
{
  "data": {
    "achievementByUid": [
      {
        "vibeCount": "1",
        "vibeReactionsList": [
          {
            "vibeName": "Inspiring",
            "vibeIntensity": 4.5,
            "reactedBy": {
              "username": "your_username"
            },
            "timestamp": "2024-01-15T10:30:00Z"
          }
        ]
      }
    ]
  }
}
```

---

## 🔑 Key Fields

### vibeCount
- Type: `String`
- Description: Total count of ALL vibes (old + new)
- **NOW UPDATED**: Includes new `ProfileContentVibe` nodes

### vibeReactionsList (NEW!)
- Type: `[ProfileContentVibeType]`
- Description: List of actual `ProfileContentVibe` nodes
- **Contains**:
  - `uid`: Vibe reaction unique ID
  - `individualVibeId`: Reference to IndividualVibe
  - `vibeName`: Name of the vibe
  - `vibeIntensity`: Intensity (1.0-5.0)
  - `reactedBy`: User who sent the vibe
  - `timestamp`: When vibe was sent
  - `isActive`: If vibe is active

### vibeList (OLD - Still Works)
- Type: `[ProfileDataVibeListType]`
- Description: Aggregated data from reaction manager
- **Note**: May need reaction manager to be updated first
- **Use `vibeReactionsList` for real-time data**

---

## ⚠️ Important Notes

1. **Use `vibeReactionsList` for real-time vibe data** - This directly queries the Neo4j nodes
2. **Use `vibeList` for aggregated analytics** - This uses the reaction manager (updated via mutation)
3. **`vibeCount` now includes both** - Old reactions + new vibes
4. **Query returns an array** - Use `achievementByUid[0]` if needed

---

## 🎉 Summary

**What's Fixed**:
- ✅ `vibeCount` now counts new vibes
- ✅ New `vibeReactionsList` field shows actual vibe nodes
- ✅ All 4 profile content types updated (Achievement, Education, Skill, Experience)
- ✅ Vibes are immediately visible after sending

**Test It Now**:
1. Send vibe with the mutation
2. Query with `vibeReactionsList` field
3. See your vibe immediately! 🎊


