from fastapi import APIRouter
from httpx import AsyncClient
from recipe_scrapers import __version__ as recipe_scraper_version

from mealie.core.release_checker import get_latest_version
from mealie.core.settings.runtime_settings import get_runtime_settings
from mealie.core.settings.static import APP_VERSION
from mealie.routes._base import BaseAdminController, controller
from mealie.schema.admin.about import AdminAboutInfo, AppStatistics, AvailableLLMModels, CheckAppConfig, LLMModel

router = APIRouter(prefix="/about")


@controller(router)
class AdminAboutController(BaseAdminController):
    @router.get("", response_model=AdminAboutInfo)
    def get_app_info(self):
        """Get general application information"""

        settings = self.settings

        return AdminAboutInfo(
            production=settings.PRODUCTION,
            version=APP_VERSION,
            versionLatest=get_latest_version(),
            demo_status=settings.IS_DEMO,
            api_port=settings.API_PORT,
            api_docs=settings.API_DOCS,
            db_type=settings.DB_ENGINE,
            db_url=settings.DB_URL_PUBLIC,
            default_group=settings.DEFAULT_GROUP,
            default_household=settings.DEFAULT_HOUSEHOLD,
            allow_signup=settings.ALLOW_SIGNUP,
            allow_password_login=settings.ALLOW_PASSWORD_LOGIN,
            token_time=settings.TOKEN_TIME,
            build_id=settings.GIT_COMMIT_HASH,
            recipe_scraper_version=recipe_scraper_version.__version__,
            enable_oidc=settings.OIDC_AUTH_ENABLED,
            oidc_redirect=settings.OIDC_AUTO_REDIRECT,
            oidc_provider_name=settings.OIDC_PROVIDER_NAME,
            enable_openai=settings.OPENAI_ENABLED,
            enable_openai_image_services=settings.OPENAI_ENABLED and settings.OPENAI_ENABLE_IMAGE_SERVICES,
        )

    @router.get("/statistics", response_model=AppStatistics)
    def get_app_statistics(self):
        return AppStatistics(
            total_recipes=self.repos.recipes.count_all(),
            uncategorized_recipes=self.repos.recipes.count_uncategorized(),  # type: ignore
            untagged_recipes=self.repos.recipes.count_untagged(),  # type: ignore
            total_users=self.repos.users.count_all(),
            total_households=self.repos.households.count_all(),
            total_groups=self.repos.groups.count_all(),
        )

    @router.get("/check", response_model=CheckAppConfig)
    def check_app_config(self):
        settings = self.settings

        return CheckAppConfig(
            email_ready=settings.SMTP_ENABLE,
            ldap_ready=settings.LDAP_ENABLED,
            base_url_set=settings.BASE_URL != "http://localhost:8080",
            is_up_to_date=APP_VERSION == "develop" or APP_VERSION == "nightly" or get_latest_version() == APP_VERSION,
            oidc_ready=settings.OIDC_READY,
            enable_openai=settings.OPENAI_ENABLED,
        )

    @router.get("/models", response_model=AvailableLLMModels)
    async def get_available_models(self):
        """Get available LLM models from the configured OpenAI-compatible API (LiteLLM)"""
        settings = self.settings

        # Get the runtime model if set, otherwise use the default
        runtime_settings = get_runtime_settings().get_settings()
        current_model = runtime_settings.llm_model or settings.OPENAI_MODEL

        if not settings.OPENAI_ENABLED:
            return AvailableLLMModels(models=[], current_model=current_model)

        base_url = settings.OPENAI_BASE_URL or "https://api.openai.com/v1"
        api_key = settings.OPENAI_API_KEY

        try:
            async with AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10.0,
                )

                if response.status_code != 200:
                    self.logger.error(f"Failed to fetch models: {response.status_code}")
                    return AvailableLLMModels(models=[], current_model=current_model)

                data = response.json()
                models = []
                for model in data.get("data", []):
                    model_id = model.get("id", "")
                    if model_id:
                        models.append(LLMModel(id=model_id, name=model_id))

                # Sort models alphabetically
                models.sort(key=lambda x: x.id)

                return AvailableLLMModels(models=models, current_model=current_model)

        except Exception as e:
            self.logger.exception(f"Error fetching models: {e}")
            return AvailableLLMModels(models=[], current_model=current_model)

    @router.post("/models", response_model=LLMModel)
    def set_llm_model(self, model: LLMModel):
        """Set the LLM model to use for all OpenAI/LiteLLM requests."""
        if not self.settings.OPENAI_ENABLED:
            raise ValueError("OpenAI is not enabled")

        get_runtime_settings().set_llm_model(model.id)
        return model

    @router.delete("/models")
    def reset_llm_model(self):
        """Reset the LLM model to the default from environment variables."""
        get_runtime_settings().set_llm_model(None)
        return {"message": "Model reset to default"}
