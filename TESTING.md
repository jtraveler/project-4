# TESTING.md

---

<h1 align="center"><strong>PromptFlow</strong>

---

![Image](static/images/README/UI%20(2).png)

## [LIVE SITE](https://mj-project-4-68750ca94690.herokuapp.com/)

## [GITHUB RESPOSITORY](https://github.com/jtraveler/project-4)

## Table of Contents

- [Manual Testing](#manual-testing)
  - [User Stories Testing](#user-stories-testing)
- [Lighthouse Testing](#lighthouse-testing)
  - [Mobile Phone](#mobile-phone)
  - [Desctop](#desctop)
- [Code Validation](#code-validation)
  - [Html](#html)
  - [CSS](#css)
  - [Python](#python)
- [Browser Compatibility](#browser-compatibility)
- [Bugs Issue](#bugs-issue)



# Manual Testing


## User Stories Testing

| **User Story** | **Testing Method** | **Expected Outcome** | **Result** |
|---------------|-------------------|---------------------|------------|
| As a visitor, I want to see an easy-to-use navigation bar to find content quickly. | Manual UI Testing | Navigation menu works well and is easy to access on all pages. | ✅ Pass |
| As a visitor, I want the site to work properly on my phone and tablet. | Responsive Testing | Website displays correctly and functions on mobile and tablet devices. | ✅ Pass |
| As a visitor, I want to browse AI prompts without needing to register. | Manual UI Testing | Homepage displays prompt gallery accessible to all visitors. | ✅ Pass |
| As a user, I want to create an account to share my own prompts. | Manual UI Testing | Registration page allows new users to sign up successfully. | ✅ Pass |
| As a user, I want to log in and out of my account safely. | Manual UI Testing | Login and logout process works correctly and securely. | ✅ Pass |
| As a user, I want to add new prompts with images to share with others. | CRUD Testing | Prompt creation form accepts text and image uploads successfully. | ✅ Pass |
| As a user, I want to edit my own prompts when I need to make changes. | CRUD Testing | Prompt editing functionality works for prompt authors only. | ✅ Pass |
| As a user, I want to remove prompts I no longer want to share. | CRUD Testing | Delete function allows authors to remove their own prompts. | ✅ Pass |
| As a user, I want to view detailed information about each prompt. | UI Testing | Prompt detail pages show all relevant information clearly. | ✅ Pass |
| As a user, I want to like prompts I find interesting or useful. | Functional Testing | Heart/like button works and updates count correctly. | ✅ Pass |
| As a user, I want to add comments to prompts to share feedback. | Functional Testing | Comment system allows users that are members to post and view comments. | ✅ Pass |
| As a user, I want to search for prompts using tags or categories. | Functional Testing | Tag filtering system displays relevant prompts correctly. | ✅ Pass |
| As a user, I want to see prompts organized in an attractive layout. | UI Testing | Masonry grid layout displays prompts in appealing columns. | ✅ Pass |
| As an admin, I want to manage user content and approve comments. | Admin Panel Testing | Admin interface allows content moderation and user management. | ✅ Pass |
| As a user, I want the site to load quickly and perform well. | Performance Testing | Lighthouse performance scores show optimized loading times. | ✅ Pass |

All testing was completed successfully, confirming that the PromptFlow platform delivers a smooth and reliable user experience across all core features.



# Lighthouse 

The following Lighthouse testing is only for the mobile versions of the pages as the tests were done with a mobile-first approach.

## Homepage
![Image](static/images/README/mobile.re.png)

## About
![Image](static/images/README/testing1.png)

## Contact Form
![Image](static/images/README/testing1.png)

## Prompt Detail
![Image](static/images/README/testing1.png)

## Edit Prompt
![Image](static/images/README/testing1.png)

## Create Prompt
![Image](static/images/README/testing1.png)

## Sign In
![Image](static/images/README/testing1.png)

## Sign Out
![Image](static/images/README/testing1.png)

## Sign Up
![Image](static/images/README/testing1.png)

## Reset Password
![Image](static/images/README/testing1.png)

## Reset Password - Email Sent
![Image](static/images/README/testing1.png)

## Search Results
![Image](static/images/README/testing1.png)

## Tags
![Image](static/images/README/testing1.png)

## 404
![Image](static/images/README/testing1.png)



# Code validation
## [Html](https://validator.w3.org/)
### index.html
![Image](static/images/README/Indexhtml.png)
### posts.html
![Image](static/images/README/postshtml.png)
### post_detail.html
![Image](static/images/README/postdetailhtml.png)
### profile.html
![Image](static/images/README/profilehtml.png)
![Image](static/images/README/editprofilehtml.png)
### edit_post.html
![Image](static/images/README/editposthtml.png)
### blogpost_confirm_delete.html
![Image](static/images/README/deteteposthtml.png)
### add_post.html
![Image](static/images/README/newposthtml.png)
### add_comment.html
![Image](static/images/README/commentposthtml.png)


## CSS
## [CSS-Valitador](#https://jigsaw.w3.org/css-validator/)
![Image](static/images/css.png)
# Python
## [pep8ci](#https://pep8ci.herokuapp.com/)
![Image](static/images/README/test1.png)
![Image](static/images/README/test2.png)
![Image](static/images/README/test3.png)
![Image](static/images/README/test4.png)
![Image](static/images/README/test5.png)
![Image](static/images/README/test6.png)
![Image](static/images/README/test7.png)
![Image](static/images/README/test8.png)
![Image](static/images/README/test9.png)
![Image](static/images/README/test10.png)
![Image](static/images/README/test11.png)
![Image](static/images/README/test12.png)
![Image](static/images/README/test13.png)
![Image](static/images/README/test14.png)
![Image](static/images/README/test15.png)
![Image](static/images/README/test16.png)

# Browser Compability

The site was tested across multiple browsers for consistency and responsiveness:

| Browser           | Result  |
|------------------|--------|
| 🌍 **Google Chrome**   | ✅ Pass  |
| 🦊 **Mozilla Firefox** | ✅ Pass  |
| 🎭 **Microsoft Edge**  | ✅ Pass  |
|🏴‍☠️ **Opera**            | ✅ Pass  |



The site maintains a **consistent design** and remains **fully responsive** across different browsers.


# Bug-Issue
## ISSUE #1 Deployment and Debugging Issues (Heroku, Cloudinary, and django-allauth)
### During the project setup and development, the following issues and resolutions were encountered:

Image Not Found (404 Error) in Admin Panel
After the initial setup, images were not loading in the admin panel, resulting in a 404 error. Updating the django-allauth and Django versions resolved this issue.

### 500 Error on Heroku After Modifying account.html

Locally, with DEBUG = True in settings.py, the application worked as expected.
However, deploying the changes to Heroku with DEBUG = False resulted in a 500 error. No error trace was visible in the terminal logs.
After updating django and django-allauth once again, the 500 error was resolved on Heroku.
Cloudinary Configuration Issue
A missing configuration in models.py related to Cloudinary was causing errors. Adding the correct command in models.py fixed the issue.
+from cloudinary_storage.storage import MediaCloudinaryStorage, +storage=MediaCloudinaryStorage(), =class BlogPost

## ISSUE #2
After upgrading texteditor reachtexteditor was changed to simple texteditor, so I lefted 4.14.0 with allert message.
![image](static/images/bug.png)

## ADVISE 
By advise in #peer-code-review in **Slack** changed Like button for a fivicon. ![Image](static/images/README/Screenshot%202025-03-04%20093035.png)

# Addition 

If a user tries to access the profile link with an account number (e.g., https://green-wisdom-99e0528945fb.herokuapp.com/profiles/user/1/) without logging in, they will encounter a 500 error. If they attempt to access the link without specifying an account number (e.g., https://green-wisdom-99e0528945fb.herokuapp.com/profiles/user/), they will be redirected to a 404 customer error page.