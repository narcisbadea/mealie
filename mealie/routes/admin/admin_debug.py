import os
import shutil

from fastapi import APIRouter, File, Form, UploadFile

from mealie.core.dependencies.dependencies import get_temporary_path
from mealie.routes._base import BaseAdminController, controller
from mealie.schema.admin.debug import DebugResponse
from mealie.schema.openai.general import OpenAIText
from mealie.services.openai import OpenAILocalImage, OpenAIService

router = APIRouter(prefix="/debug")


@controller(router)
class AdminDebugController(BaseAdminController):
    @router.post("/openai", response_model=DebugResponse)
    @router.post("/ai", response_model=DebugResponse, include_in_schema=False)
    async def debug_openai(
        self,
        image: UploadFile | None = File(None),
        model: str | None = Form(None),
    ):
        if not self.settings.OPENAI_ENABLED:
            return DebugResponse(success=False, response="AI is not enabled")
        if image and not self.settings.OPENAI_ENABLE_IMAGE_SERVICES:
            return DebugResponse(success=False, response="Image was provided, but AI image services are not enabled")

        with get_temporary_path() as temp_path:
            if image:
                with temp_path.joinpath(image.filename).open("wb") as buffer:
                    shutil.copyfileobj(image.file, buffer)
                local_image_path = temp_path.joinpath(image.filename)
                local_images = [OpenAILocalImage(filename=os.path.basename(local_image_path), path=local_image_path)]
            else:
                local_images = None

            try:
                openai_service = OpenAIService(model=model)
                prompt = openai_service.get_prompt("debug")

                message = "Hello, checking to see if I can reach you."
                if local_images:
                    message = f"{message} Here is an image to test with:"

                response = await openai_service.get_response(
                    prompt, message, response_schema=OpenAIText, images=local_images
                )

                if not response:
                    raise Exception("No response received from AI")

                return DebugResponse(
                    success=True,
                    response=f'AI is working with model "{openai_service.model}". Response: "{response.text}"',
                )

            except Exception as e:
                self.logger.exception(e)
                return DebugResponse(
                    success=False,
                    response=f'AI request failed. Full error has been logged. {e.__class__.__name__}: "{e}"',
                )
