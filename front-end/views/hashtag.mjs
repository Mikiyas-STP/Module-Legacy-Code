import {renderOne, renderEach, destroy} from "../lib/render.mjs";
import {
  state,
  apiService,
  getLogoutContainer,
  getLoginContainer,
  getTimelineContainer,
  getHeadingContainer,
} from "../index.mjs";
import {createLogin, handleLogin} from "../components/login.mjs";
import {createLogout, handleLogout} from "../components/logout.mjs";
import {createBloom} from "../components/bloom.mjs";
import {createHeading} from "../components/heading.mjs";

// Hashtag view: show all tweets containing this tag

function hashtagView(hashtag) {
  if (state.currentHashtag !== hashtag) {
    state.currentHashtag = hashtag;
    state.hashtagBlooms = null;
    apiService.getBloomsByHashtag(hashtag);
  }

  destroy();

  renderOne(
    state.isLoggedIn,
    getLogoutContainer(),
    "logout-template",
    createLogout
  );
  document
    .querySelector("[data-action='logout']")
    ?.addEventListener("click", handleLogout);
  renderOne(
    state.isLoggedIn,
    getLoginContainer(),
    "login-template",
    createLogin
  );
  document
    .querySelector("[data-action='login']")
    ?.addEventListener("click", handleLogin);

  renderOne(
    state.currentHashtag,
    getHeadingContainer(),
    "heading-template",
    createHeading
  );

  const timelineContainer = getTimelineContainer();
if (state.hashtagBlooms === null) {
    timelineContainer.innerHTML = "<p>Loading...</p>"; // or a spinner
} else {
    renderEach(
        state.hashtagBlooms,
        timelineContainer,
        "bloom-template",
        createBloom
    );
}
}

export {hashtagView};
