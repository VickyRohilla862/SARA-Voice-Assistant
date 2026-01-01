import asyncio
from random import randint
from PIL import Image
import requests
from dotenv import get_key
import os
from time import sleep

# function to open images based on a given prompt
def open_images(prompt):
    folder_path = r'Data/Images/' # folder where the images are stored
    prompt = prompt.replace(' ', '_') # replace spaces in prompt with underscores
    # generate the file name for the image
    Files = [f'{prompt}.jpg' for i in range(1)]
    for jpg_file in Files:
        image_path = os.path.join(folder_path, jpg_file)
        try:
            # try to open and display the image
            img = Image.open(image_path)
            print(f'Opening image: {image_path}')
            img.show()
            sleep(5) # pause for 5 second before showing the next image
        except IOError:
            print(f'Unable to open {image_path}')

# API details for the hugging face stable diffusion model
API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"

headers = {'Authorization': f"Bearer {get_key('.env','HuggingFaceAPIKey')}"}

# async function to send a query to the Hugging Face API
async def query(payload):
    response = await asyncio.to_thread(
        requests.post,
        API_URL,
        headers=headers,
        json=payload
    )

    # If response is JSON, it's an error
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        print("API Error:", response.json())
        return None

    return response.content


# async fucntion to generate images based on the given prompt
async def generate_images(prompt:str):
    tasks = []
    # create 1 image generation task
    for _ in range(1):
        payload = {
            'inputs': f'{prompt}, quality=4K, sharpness=maximum, Ultra High Details, high resolution, non-distorted, no extra limbs, realistic faceial features, realistic anatomy, realistic fingers, try again if there is any problem in the image, seed={randint(0,1000000)}',
        }
        task = asyncio.create_task(query(payload))
        tasks.append(task)

    # wait for all tasks to complete
    image_bytes_list = await asyncio.gather(*tasks)

    # save the generated image to files
    for i, image_bytes in enumerate(image_bytes_list):
        if image_bytes is None:
            continue

        with open(
            fr'Data/Images/{prompt.replace(" ", "_")}.jpg',
            'wb'
        ) as f:
            f.write(image_bytes)


# wrapper function to generate and open images
def GenerateImages(prompt:str):
    asyncio.run(generate_images(prompt)) # run the async image generation
    open_images(prompt) # open the generated images

# main loop to monitor for image generation requests
while True:
    try:
        with open(r'Frontend/Files/ImageGeneration.data','r') as f:
            Data = f.read().strip()

        parts = Data.split(',')
        if len(parts) != 2:
            sleep(1)
            continue

        Prompt = parts[0].strip()
        Status = parts[1].strip()

        if Status == 'True':
            print('Generating Image...')
            with open(r'Frontend/Files/ImageGeneration.data', 'w') as f:
                f.write('False,False')
            GenerateImages(Prompt)

        else:
            sleep(1)

    except Exception as e:
        print(f'Error: {e}')