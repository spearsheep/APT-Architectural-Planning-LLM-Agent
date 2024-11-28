from langchain.llms import AzureOpenAI
from langchain.llms import OpenAI
from langchain.chains import LLMChain
import langchain
from langchain.prompts import PromptTemplate
# from langchain.prompts import ChatPromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import SimpleSequentialChain
# from langchain_openai import AzureChatOpenAI
from langchain.chains import SequentialChain
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_community.callbacks import get_openai_callback
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import base64
from langchain.memory import ConversationBufferMemory
import httpx
from langchain_openai import AzureChatOpenAI
from fixJson import fix_json_response
import json
from memory import MemoryDatabase
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
import base64
import requests
class LLMDecisionMaker:
    def __init__(self, llm):
        self.llm = llm 
        # Initialize the memory database
        self.memoryDatabase = MemoryDatabase()
        self.retriever = self.memoryDatabase.vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 1})
        self.observationPrompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert in Minecraft, providing detailed and concise summaries based on provided in-game observations and, if applicable, reflects upon previous failed actions."),
    ("user", """
    Please analyze the following Minecraft state and observation details:
     
    - Previous failed action plan: {failedPlan} 
    - Health: {health}
    - Hunger: {hunger}
    - Position: {position}
    - Inventory (xx/36): {inventory}
    - Nearby Entities: {nearbyEntities}

    Generate a coherent and natural language summary covering all the provided details. If a previous plan failed, reflect on it and provide additional suggestions for how to successfully execute it this time.
    
    - For inventory items like {{'name': 'stick', 'count': 8, 'slot': 10}}, describe as: "I have 8 sticks in slot 10."
    - For nearby entities like {{'name': 'chicken', 'type': passive mobs, 'position': Vec3 {{ x: -36.3, y: 74, z: -34.5 }}}}, describe as: "There is a chicken at coordinates -36.3, 74, -34.5." If a player is at the same coordinates as you, do not report it.

    Ensure the summary is clear, accurate, and reflective of the current game state.
    """)
])

        self.planPrompt = ChatPromptTemplate.from_messages([
    ("system", """
    You are a Minecraft expert specializing in generating actionable sequences to accomplish tasks based on the bot's current status and available actions.

    ### Available Actions and Examples

    1. **pathfinding(goalPosition, findPlayer=None)**:
       - **Description**: Directs the bot to move to a specified position using pathfinding.
       - **Example**:
         ```python
         goalPosition = vec3(-260, 37, 450)
         self.actions.pathfinding(goalPosition, findPlayer=True)
         ```

    2. **placeBlockAt(self, name, position):**:
       - **Description**: Places a specified item from the bot’s inventory at a given position.
       - **Example**:
         ```python
         self.actions.placeBlockAt('oak_planks', self.actions.getPosition())
         ```

    3. **mineBlock(name, count=1)**:
       - **Description**: Commands the bot to locate and mine a specified block type up to a given count.
       - **Example**:
         ```python
         self.actions.mineBlock('spruce_fence', 5)
         ```

    4. **craftItem(name, amount, useCraftingTable=True)**:
       - **Description**: Crafts a specified item using resources from the bot's inventory. The `useCraftingTable` argument determines if a crafting table is required.
          - **useCraftingTable=True**: The bot will find and use the nearest crafting table, necessary for items requiring it.
          - **useCraftingTable=False**: The bot will craft the item directly in its inventory for recipes that do not need a crafting table.
          -  'amount' refers to how many times you wish to perform the operation. If you want to craft planks into 8 sticks, which is two operation, then you would set count to 2
       - **Example**:
         ```python
         self.actions.craftItem('crafting_table', 1, False)
         self.actions.craftItem('wooden_pickaxe', 1, True)
         ```

    5. **smeltItems(itemName, fuelName, count)**:
       - **Description**: Smelts a specified item using a furnace with a given fuel and quantity.
       - **Example**:
         ```python
         self.actions.smeltItems('chicken', 'coal', 5)
         ```

    6. **observe(distance)**:
       - **Description**: Observes the environment within a specified distance, gathering information about nearby blocks and entities.
       - **Example**:
         ```python
         self.actions.observe(15)
         ```

    7. **getState()**:
       - **Description**: Retrieves the bot's current state, including health, hunger, and inventory items.
       - **Example**:
         ```python
         self.actions.getState()
         ```

    8. **moveToChest(chestPosition=None)**:
       - **Description**: Moves the bot to a chest, either by searching nearby or to a specified position, and returns the chest block.
       - **Example**:
         ```python
         chestBlock = self.actions.moveToChest()
         ```

    9. **listItemsInChest(chestBlock)**:
       - **Description**: Lists and returns the items stored in a specified chest.
       - **Example**:
         ```python
         chest = self.actions.listItemsInChest(chestBlock)
         ```

    10. **depositItemIntoChest(chestBlock, itemsToDeposit)**:
        - **Description**: Deposits specified items from the bot's inventory into a given chest.
        - **Example**:
          ```python
          itemsToDeposit = {{'coal': 2, 'chicken': 4}}
          self.actions.depositItemIntoChest(chestBlock, itemsToDeposit)
          ```

    11. **getItemsFromChest(chestBlock, itemsToGet)**:
        - **Description**: Retrieves specified items from a chest and adds them to the bot's inventory.
        - **Example**:
          ```python
          itemsToGet = {{'oak_planks': 40}}
          self.actions.getItemsFromChest(chestBlock, itemsToGet)
          ```

    12. **killMob(mobName)**:
        - **Description**: Uses pathfinding to locate and kill the nearest mob of a specified type.
        - **Example**:
          ```python
          self.actions.killMob('pig')
          ```
     

     13.**def getPosition(self)**:
        - **Description**: return the agent's current position
        - **Example**:
          ```python
          self.actions.getPosition()
          ```     

    """),
    ("user", """
    The following is a summary of my current state and observations:
    *State and observations*:{observation}
    The following task needs to be accomplished in Minecraft:
    **Task**: {task}
     
    here are some relevant plans from past experiences that were effective under thier contextual observations:
    {retrievedPlans}
  

    Considering these, please generate a new plan to accomplish the task.
     
    1. Be flexible with the planning based on my state and observations. For instance, if I already have the required resources for completing the task, then the action sequences can be simplified.
     
    Output the actions into a compact JSON format on a single line without whitespace like the following:
     "Action 1":"self.actions.mineBlock('oak_log', 2)",
     "Action 2":"self.actions.craftItem('oak_planks', 10, False)"
    """)
])
       

        self.observationChain = LLMChain(llm=self.llm, prompt=self.observationPrompt, output_key="observation", memory=None)
        self.planChain = LLMChain(llm=self.llm, prompt=self.planPrompt, output_key="plan", memory=None)

        self.overallChain = SequentialChain(
            chains=[self.observationChain, self.planChain],
            input_variables=["task", 'health', 'hunger', 'inventory', 'position', 'nearbyEntities','retrievedPlans','failedPlan'],
            output_variables=["observation", "plan"],
            verbose=True
        )

    def generatePlan(self, task, state, position, observationSpace):

        # Step 1: Retrieve similar past plans
    
        retrievedDocs = self.retriever.invoke(task, filter={"source": "news"})

        # Combine retrieved plans into a single string
        retrievedContent = "\n".join([doc.page_content for doc in retrievedDocs])

        result = self.overallChain.invoke(input={
            "task": task,
            "health": state['health'],
            "position": position,
            "hunger": state['food'],
            "inventory": state['inventory'],
            'nearbyEntities': observationSpace['nearbyEntities'],
            'failedPlan':observationSpace['failedPlan'],
            'retrievedPlans': retrievedContent
        })
        return fix_json_response(result['plan'])

    


class singleAgentDecisionMaker:
    def __init__(self, llm):
        self.llm = llm 
        # Initialize the memory database
        self.memoryDatabase = MemoryDatabase()
        self.retriever = self.memoryDatabase.vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 1})
        self.observationPrompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert in Minecraft, providing detailed and concise summaries based on provided in-game observations and, if applicable, reflects upon previous failed actions."),
    ("user", """
    Please analyze the following Minecraft state and observation details:
     
    - Previous failed action plan: {failedPlan} 
    - Health: {health}
    - Hunger: {hunger}
    - Position: {position}
    - Inventory (xx/36): {inventory}
    - Nearby Entities: {nearbyEntities}

    Generate a coherent and natural language summary covering all the provided details. If a previous plan failed, reflect on it and provide additional suggestions for how to successfully execute it this time.
    
    - For inventory items like {{'name': 'stick', 'count': 8, 'slot': 10}}, describe as: "I have 8 sticks in slot 10."
    - For nearby entities like {{'name': 'chicken', 'type': passive mobs, 'position': Vec3 {{ x: -36.3, y: 74, z: -34.5 }}}}, describe as: "There is a chicken at coordinates -36.3, 74, -34.5." If a player is at the same coordinates as you, do not report it.

    Ensure the summary is clear, accurate, and reflective of the current game state.
    """)
])

        self.planPrompt = ChatPromptTemplate.from_messages([
    ("system", """
    You are a Minecraft expert specializing in generating actionable sequences to collect the all materials needed in the provided architecture layout with available actions below

    ### Available Actions and Examples

    1. **pathfinding(goalPosition, findPlayer=None)**:
       - **Description**: Directs the bot to move to a specified position using pathfinding.
       - **Example**:
         ```python
         goalPosition = vec3(-260, 37, 450)
         self.actions.pathfinding(goalPosition, findPlayer=True)
         ```

    2. **placeBlockAt(self, name, position):**:
       - **Description**: Places a specified item from the bot’s inventory at a given position.
       - **Example**:
         ```python
         self.actions.placeBlockAt('oak_planks', self.actions.getPosition())
         ```

    3. **mineBlock(name, count=1)**:
       - **Description**: Commands the bot to locate and mine a specified block type up to a given count.
       - **Example**:
         ```python
         self.actions.mineBlock('spruce_fence', 5)
         ```

    4. **craftItem(name, amount, useCraftingTable=True)**:
       - **Description**: Crafts a specified item using resources from the bot's inventory. The `useCraftingTable` argument determines if a crafting table is required.
          - **useCraftingTable=True**: The bot will find and use the nearest crafting table, necessary for items requiring it.
          - **useCraftingTable=False**: The bot will craft the item directly in its inventory for recipes that do not need a crafting table.
          -  'amount' refers to how many times you wish to perform the operation. If you want to craft planks into 8 sticks, which is two operation, then you would set count to 2
       - **Example**:
         ```python
         self.actions.craftItem('crafting_table', 1, False)
         self.actions.craftItem('wooden_pickaxe', 1, True)
         ```

    5. **smeltItems(itemName, fuelName, count)**:
       - **Description**: Smelts a specified item using a furnace with a given fuel and quantity.
       - **Example**:
         ```python
         self.actions.smeltItems('chicken', 'coal', 5)
         ```

    6. **observe(distance)**:
       - **Description**: Observes the environment within a specified distance, gathering information about nearby blocks and entities.
       - **Example**:
         ```python
         self.actions.observe(15)
         ```

    7. **getState()**:
       - **Description**: Retrieves the bot's current state, including health, hunger, and inventory items.
       - **Example**:
         ```python
         self.actions.getState()
         ```

    8. **moveToChest(chestPosition=None)**:
       - **Description**: Moves the bot to a chest, either by searching nearby or to a specified position, and returns the chest block.
       - **Example**:
         ```python
         chestBlock = self.actions.moveToChest()
         ```

    9. **listItemsInChest(chestBlock)**:
       - **Description**: Lists and returns the items stored in a specified chest.
       - **Example**:
         ```python
         chest = self.actions.listItemsInChest(chestBlock)
         ```

    10. **depositItemIntoChest(chestBlock, itemsToDeposit)**:
        - **Description**: Deposits specified items from the bot's inventory into a given chest.
        - **Example**:
          ```python
          itemsToDeposit = {{'coal': 2, 'chicken': 4}}
          self.actions.depositItemIntoChest(chestBlock, itemsToDeposit)
          ```

    11. **getItemsFromChest(chestBlock, itemsToGet)**:
        - **Description**: Retrieves specified items from a chest and adds them to the bot's inventory.
        - **Example**:
          ```python
          itemsToGet = {{'oak_planks': 40}}
          self.actions.getItemsFromChest(chestBlock, itemsToGet)
          ```

    12. **killMob(mobName)**:
        - **Description**: Uses pathfinding to locate and kill the nearest mob of a specified type.
        - **Example**:
          ```python
          self.actions.killMob('pig')
          ```
     

     13.**def getPosition(self)**:
        - **Description**: return the agent's current position
        - **Example**:
          ```python
          self.actions.getPosition()
          ```     

    """),
    ("user", """
    The following is a summary of my current state and observations:
    *State and observations*:{observation}
    The following blueprint's materials need to be collected in Minecraft:
    **Layout**: {layout}
     
    here are some relevant plans from past experiences that were effective under thier contextual observations:
    {retrievedPlans}
  

    Considering these, please generate a new plan to only collect the materials, dont build the architecture.
     
    1. Be flexible with the planning based on my state and observations. For instance, if I already have the required resources, then the action sequences can be simplified.
     
    Output the actions into a compact JSON format on a single line without whitespace like the following:
     "Action 1":"self.actions.mineBlock('oak_log', 2)",
     "Action 2":"self.actions.craftItem('oak_planks', 10, False)"
    """)
])
        
        self.buildPrompt = ChatPromptTemplate.from_messages([
    ("system", """
You are recognized as an expert in Minecraft and coding. Your task is to write Python code using the Mineflayer library to generate layouts for specific structures in Minecraft. For example, here's a detailed task to build an 8x8 room with a window panel and a bed:

def generate_house_layout(start_pos, width, length, height, door_pos, window_positions, crafting_table_pos):
    layout = []

    # Floor construction
    for x in range(width):
        for z in range(length):
            layout.append(('oak_planks', start_pos.offset(x, 0, z)))

    # Wall construction
    for x in range(width):
        for z in range(length):
            if x in [0, width-1] or z in [0, length-1]:
                for y in range(1, height):
                    if (x, z) == door_pos and y < 3:
                        if y == 1:
                            layout.append(('oak_door', start_pos.offset(x, y, z)))
                    elif (x, z) in window_positions and y == 1:
                        layout.append(('glass_pane', start_pos.offset(x, y, z)))
                    else:
                        layout.append(('oak_planks', start_pos.offset(x, y, z)))

    # Roof construction
    for x in range(width):
        for z in range(length):
            layout.append(('oak_planks', start_pos.offset(x, height, z)))

    # Crafting table placement
    layout.append(('crafting_table', start_pos.offset(*crafting_table_pos)))

    return layout

# Example usage to generate the house layout
start_pos = self.bot.entity.position.floor()
# The returned layout's variable name must be layout like below
layout = generate_house_layout(start_pos, 3, 3, 3, (1, 0), [(1, 2)], (1, 1, 1))
self.actions.buildStructure(layout, mode = 'survival')


    """),

    ("user", """
    Please provide the code for this structure:{structure}. Do not import mineflayer or vec3
     Ensure the generated code is properly indented and formatted as a complete Python script. Only include the code and output the code into a compact JSON format on a single line without whitespace like the following:
     'code':'code here'
    """)
])
       
        self.buildChain = LLMChain(llm=llm, prompt= self.buildPrompt ,output_key="blueprint",memory=None)
        self.observationChain = LLMChain(llm=self.llm, prompt=self.observationPrompt, output_key="observation", memory=None)
        self.planChain = LLMChain(llm=self.llm, prompt=self.planPrompt, output_key="plan", memory=None)

        self.overallChain = SequentialChain(
            chains=[self.observationChain, self.planChain],
            input_variables=["layout", 'health', 'hunger', 'inventory', 'position', 'nearbyEntities','retrievedPlans','failedPlan','structure'],
            output_variables=["observation", "plan"],
            verbose=True
        )

    def generatePlan(self, structure, state, position, observationSpace):

        # Step 1: Retrieve similar past plans
    
        retrievedDocs = self.retriever.invoke(structure, filter={"source": "news"})

        # Combine retrieved plans into a single string
        retrievedContent = "\n".join([doc.page_content for doc in retrievedDocs])

        buildResult = self.buildChain.invoke(input={
            "structure": structure,
        })
        jsonResult = fix_json_response(buildResult['blueprint'])

        result = self.overallChain.invoke(input={
            "layout": jsonResult['code'],
            "health": state['health'],
            "position": position,
            "hunger": state['food'],
            "inventory": state['inventory'],
            'nearbyEntities': observationSpace['nearbyEntities'],
            'failedPlan':observationSpace['failedPlan'],
            'retrievedPlans': retrievedContent,
            'structure':structure
        })
        actions_dict = fix_json_response(result['plan'])
        actions_dict['code'] =jsonResult['code']
        print(actions_dict)
        return actions_dict
    



class ArchitectLLMAlgorithm:
    def __init__(self, llm):
        self.llm = llm
        self.memoryDatabase = MemoryDatabase(collection_name="Architect", persist_directory="./memory_databases")
        self.retriever = self.memoryDatabase.vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 1})
        self.memory = ConversationBufferMemory(input_key="structure")


        self.buildPrompt = ChatPromptTemplate.from_messages([
    ("system", """
You are an expert in both Minecraft and Python coding. Your task is to generate Python code that creates layouts for Minecraft structures as a list of tuples.

The structure layout should be represented in the following way:
- Each tuple contains:
  1. The block type (e.g., 'oak_planks', 'glass_pane', 'oak_door').
  2. The exact 3D position of the block, represented by a vec3 object with x, y, and z coordinates.

The layout should follow this format:
[
    ('block_type', start_pos.offset(x, y, z)),
    ('block_type', start_pos.offset(x, y, z)),
    ('block_type', start_pos.offset(x, y, z))
]

Important Notes:
- You do not need to manually define every block's coordinates. Instead, provide an efficient and reusable code that generates the layout dynamically, based on the starting position.
- The variable storing the layout must be named layout. 
- Do not append 'air' to the layout

#always start the code with this
start_pos = self.bot.entity.position.floor()
#layout generation code that returns the layout
# ...
# The output always ends with the layout being passed into the following method
self.actions.buildStructure(layout, mode='creative')
"""
),

    ("user", """
    Here is a possibly relevant plan from past experiences that were effective under their contexts(could be None). If the task described isn't relevant, don't reference it. If it is highly relevant or the same, reference as much as you can:
    {retrievedPlans}
    Please provide the code for this structure:{structure}. 
    1.Do not import mineflayer or vec3
    2.Do not miss any components
     Ensure the generated code is properly indented and formatted as a complete Python script. Only include the code and output the code into a compact JSON format on a single line without whitespace the key is 'code' and the value is the actual code.
    """)
])
        
        self.sizePrompt = ChatPromptTemplate.from_messages([
    ("user", """
Given the following layout code: {blueprint}, calculate the 3D dimensions of the structure. Provide the size as a `vec3` in the format (x, y, z), where:
- `x` is the width,
- `y` is the height,
- `z` is the length.

Output the result in a compact JSON format on a single line without whitespace, like this:
"size":"vec3(x, y, z)"
    """)
])


        self.reflectionPrompt  = """
        You are an expert in both Minecraft structure generation and Python coding. Below is the current imperfect blueprint code used to generate a Minecraft structure, along with a description of the intended structure and an image of what was generated by the current code.

        ### Structure Description:
        {structure}

        ### Current Blueprint Code:
        {blueprint}

        ### Task: Generate the following features
        1. "reflection": "Analyze why the current blueprint code does not successfully generate the structure as described. Compare the structure description with both the image and the code itself. Issues may arise either from discrepancies in the visual appearance of the generated structure compared to the description, or from errors in the code's syntax that prevent it from running. Keep this concise"
        2. "code": "Provide an improved, optimized version of the blueprint code that accurately aligns with the structure description and resolves any issues in the current code."


        #always start the code with this
        start_pos = self.bot.entity.position.floor()
        #layout generation code that returns the layout
        # ...
        # The output always ends with the layout being passed into the following method
        self.actions.buildStructure(layout, mode='creative')


        Ensure the generated code is properly indented and formatted as a complete Python script. Include the code and reasoning into a compact JSON format on a single line without whitespace where we have two keys "reflection" and 'code' and the value is the corresponding output.
        """

        
        self.sizeChain = LLMChain(llm=llm, prompt= self.sizePrompt ,output_key="size")
        self.buildChain = LLMChain(llm=llm, prompt= self.buildPrompt ,output_key="blueprint")
        self.overallChain = SequentialChain(
            chains=[self.buildChain,self.sizeChain],
            input_variables=["structure", 'retrievedPlans'],
            output_variables=["blueprint",'size'],
            verbose=True
        )


    def intepretImage(self,imageURL):
        message = HumanMessage(
            content=[
                {"type": "text", 
                "text": """
        Please describe the structure in the provided image translated with the following minecraft details:

        1. **Components and positioning**: List all individual elements (e.g., blocks, materials, windows, doors, etc.) used in the structure and describe the position of each component relative to the entire structure. Use directional terms (e.g., north, south, east, west) and relative distances if necessary.
        2. **Dimensional Layout**: Provide the overall dimensions of the structure (length, width, height) in a clear 3D format.
        3. **Description**: Summarize the purpose and design of the structure (e.g., a house, tower, etc.), including any notable features or unique aspects of its construction.
      

        Please ensure the description is clear, precise, and professional, making it easy to recreate the structure programmatically.
                """
                },
                {"type": "image_url", "image_url": {"url": imageURL}},
            ],
        )
        with get_openai_callback() as cb:
            response = self.llm.invoke([message])
            print (cb)
            print(response.content)
        return response.content
    
    def intepretText(self, text):
        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": f"""
    Please translate the structure in the provided text with the following Minecraft details:

    1. **Components and positioning**: List all individual elements (e.g., blocks, materials, windows, doors, etc.) used in the structure and describe the position of each component relative to the entire structure. 
    2. **Dimensional Layout**: Provide the overall dimensions of the structure (length, width, height).
    3. **Description**: Summarize the purpose and design of the structure (e.g., a house, tower, etc.), Outline the most logical construction sequence, taking into account how building certain parts first could obstruct access to other areas.

    Please ensure the description is clear, precise, and professional, making it easy to recreate the structure programmatically.

    Here is the provided text description:
    {text}
                    """
                }
            ]
        )

        # Use the LLM to process the message and invoke the interpretation
        with get_openai_callback() as cb:
            response = self.llm.invoke([message])
            print(cb)
            print(response.content)

        return response.content

    def selfReflect(self, image_paths, structure, blueprint):
        api_key = "sk-proj-K3Ezxr5EfkFTVqoHR9x6T3BlbkFJbNXk2FoiqG65C6t6Vr94"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        # Start building the message content with the blueprint and structure description
        message_content = [
            {
                "type": "text",
                "text": self.reflectionPrompt.format(blueprint=blueprint, structure=structure)
            }
        ]

        # Loop through each image path and add the base64 encoded image to the content
        for image_path in image_paths:
            # Encode the image as base64
            base64_image = self.encode_image(image_path)
            # Append the image to the message content
            message_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            })

        # Construct the payload with all images and the formatted text
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": message_content
                }
            ],
            "max_tokens": 10000
        }

        # Send the request to OpenAI's API
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        
        # Extract and process the output
        output = fix_json_response(response.json()['choices'][0]['message']['content'])
        print(output)
        return output['code'], output['reflection']
    

    def encode_image(self,image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')


    def generateBlueprint(self, structure=None, useImage=False, imageUrl=None,memory=True):
        
        if not useImage:
            if memory:
                # Case 1: If using a textual description of the structure
                retrievedDocs = self.retriever.invoke(structure, filter={"source": "news"})

                # Combine retrieved plans into a single string
                retrievedPlans = "\n".join([doc.page_content for doc in retrievedDocs])
                print(f'This is the retrieved plan{retrievedPlans}')
            else:
                retrievedPlans = 'None'
            if structure is None:
                raise ValueError("A structure description must be provided when useImage is False.")
            textDescription = self.intepretText(structure)
            with get_openai_callback() as cb:
                # Invoke the chain with the text-based structure input
                buildResult = self.overallChain.invoke(input={
                    "structure": textDescription,
                    'retrievedPlans':retrievedPlans,
                })
                print(cb)
            
            print(buildResult['blueprint'])
            jsonResult = fix_json_response(buildResult['blueprint'])
            sizeResult = fix_json_response(buildResult['size'])
            
            return jsonResult['code'], sizeResult['size']
        
        # Case 2: If using an image URL to generate the structure
        else:
            if imageUrl is None:
                raise ValueError("An image URL must be provided when useImage is True.")
            
            # Interpret the image into a structure description
            imageDescription = self.intepretImage(imageUrl)
            self.imageDescription =imageDescription
            if memory:
                retrievedDocs = self.retriever.invoke(self.imageDescription, filter={"source": "news"})
                retrievedPlans = "\n".join([doc.page_content for doc in retrievedDocs])
                print(f'This is the retrieved plan{retrievedPlans}')
            else:  
                retrievedPlans = 'None'
            with get_openai_callback() as cb:
                # Invoke the chain with the image-based structure description
                buildResult = self.overallChain.invoke(input={
                    "structure": imageDescription,
                    'retrievedPlans':retrievedPlans,
                })
                print(cb)
                
            print(buildResult['blueprint'])
            jsonResult = fix_json_response(buildResult['blueprint'])
            sizeResult = fix_json_response(buildResult['size'])
            
            return jsonResult['code'], sizeResult['size']
        
   



    
    



class GathererLLMAlgorithm:
    def __init__(self, llm):
        self.llm = llm
        self.memoryDatabase = MemoryDatabase(collection_name="Gatherer", persist_directory="./memory_databases")
        self.retriever = self.memoryDatabase.vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 1})
        self.materialPrompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert in mathematics, coding, and Minecraft. Your task is to analyze a given layout code and accurately determine the required Minecraft materials, including their correct item names and quantities."),
    ("user", """
    Below is the layout code: {layout}
     
    Please provide a list of all Minecraft items needed to execute this layout, along with the exact quantity required for each item. Ensure that each item name is precise and follows Minecraft’s naming conventions.

    Example format: 5 'oak_planks', 1 'crafting_table'
    """)
])

        self.observationPrompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert in Minecraft, responsible for providing detailed and concise summaries based on the in-game observations provided to you. When applicable, also reflect on previous failed actions.To determine if an action in a sequence was successful, the system uses a success indicator. For example, ('Action 1', 'self.actions.mineBlock("oak_log", 9)', True) means the action to mine 9 oak logs was successful. Conversely, ('Action 2', 'self.actions.craftItem("oak_planks", 9, False)', False) indicates that the crafting attempt failed. The final True or False in each case shows whether the action succeeded or not."""),
    ("user", """
    Please analyze the following Minecraft state and observation details:
     
    - Previous failed action plan: {failedPlan} 
    - Health: {health}
    - Hunger: {hunger}
    - Position: {position}
    - Inventory (xx/36): {inventory}
    - Nearby Entities: {nearbyEntities}

    Generate a coherent and natural language summary covering all the provided details. If a previous plan failed, reflect on it and provide additional suggestions for how to successfully execute it this time.
    
    - For inventory items like {{'name': 'stick', 'count': 8, 'slot': 10}}, describe as: "I have 8 sticks in slot 10."
    - For nearby entities like {{'name': 'chicken', 'type': passive mobs, 'position': Vec3 {{ x: -36.3, y: 74, z: -34.5 }}}}, describe as: "There is a chicken at coordinates -36.3, 74, -34.5." If a player is at the same coordinates as you, do not report it.

    Ensure the summary is clear, accurate, and reflective of the current game state.
    """)
])

        self.collectPrompt = ChatPromptTemplate.from_messages([
    ("system", """
    You are a Minecraft expert specializing in generating actionable sequences to collect the all materials needed in the provided material list

    ### Available Actions and Examples

    1. **pathfinding(goalPosition, findPlayer=None)**:
       - **Description**: Directs the bot to move to a specified position using pathfinding.
       - **Example**:
         ```python
         goalPosition = vec3(-260, 37, 450)
         self.actions.pathfinding(goalPosition, findPlayer=True)
         ```

    2. **placeBlockAt(self, name, position):**:
       - **Description**: Places a specified item from the bot’s inventory at a given position.
       - **Example**:
         ```python
         self.actions.placeBlockAt('oak_planks', self.actions.getPosition())
         ```

    3. **mineBlock(name, count=1)**:
       - **Description**: Commands the bot to locate and mine a specified block type up to a given count.
       - **Example**:
         ```python
         self.actions.mineBlock('spruce_fence', 5)
         ```

    4. **craftItem(name, amount, useCraftingTable=True)**:
       - **Description**: Crafts a specified item using resources from the bot's inventory. The `useCraftingTable` argument determines if a crafting table is required.
          - **useCraftingTable=True**: The bot will find and use the nearest crafting table, necessary for items requiring it.
          - **useCraftingTable=False**: The bot will craft the item directly in its inventory for recipes that do not need a crafting table.
          -  'amount' refers to how many times you wish to perform the operation. If you want to craft planks into 8 sticks, which is two operation, then you would set count to 2
       - **Example**:
         ```python
         self.actions.craftItem('crafting_table', 1, False)
         self.actions.craftItem('wooden_pickaxe', 1, True)
         ```

    5. **smeltItems(itemName, fuelName, count)**:
       - **Description**: Smelts a specified item using a furnace with a given fuel and quantity.
       - **Example**:
         ```python
         self.actions.smeltItems('chicken', 'coal', 5)
         ```

    6. **observe(distance)**:
       - **Description**: Observes the environment within a specified distance, gathering information about nearby blocks and entities.
       - **Example**:
         ```python
         self.actions.observe(15)
         ```

    7. **getState()**:
       - **Description**: Retrieves the bot's current state, including health, hunger, and inventory items.
       - **Example**:
         ```python
         self.actions.getState()
         ```

    8. **moveToChest(chestPosition=None)**:
       - **Description**: Moves the bot to a chest, either by searching nearby or to a specified position, and returns the chest block.
       - **Example**:
         ```python
         chestBlock = self.actions.moveToChest()
         ```

    9. **listItemsInChest(chestBlock)**:
       - **Description**: Lists and returns the items stored in a specified chest.
       - **Example**:
         ```python
         chest = self.actions.listItemsInChest(chestBlock)
         ```

    10. **depositItemIntoChest(chestBlock, itemsToDeposit)**:
        - **Description**: Deposits specified items from the bot's inventory into a given chest.
        - **Example**:
          ```python
          itemsToDeposit = {{'coal': 2, 'chicken': 4}}
          self.actions.depositItemIntoChest(chestBlock, itemsToDeposit)
          ```

    11. **getItemsFromChest(chestBlock, itemsToGet)**:
        - **Description**: Retrieves specified items from a chest and adds them to the bot's inventory.
        - **Example**:
          ```python
          itemsToGet = {{'oak_planks': 40}}
          self.actions.getItemsFromChest(chestBlock, itemsToGet)
          ```

    12. **killMob(mobName)**:
        - **Description**: Uses pathfinding to locate and kill the nearest mob of a specified type.
        - **Example**:
          ```python
          self.actions.killMob('pig')
          ```
     

     13.**def getPosition(self)**:
        - **Description**: return the agent's current position
        - **Example**:
          ```python
          self.actions.getPosition()
          ```     

    """),
    ("user", """
    The following is a summary of my current state and observations:
    *State and observations*:{observation}
    The following blueprint's materials need to be collected in Minecraft:
    **Materials**: {materials}
     
    here are some relevant plans from past experiences that were effective under thier contextual observations:
    {retrievedPlans}
  

    Considering these, please generate a new plan to only collect the materials, dont build the architecture.
     
    1. Be flexible with the planning based on my state and observations. For instance, if I already have the required resources, then the action sequences can be simplified.
     
    Output the actions into a compact JSON format on a single line without whitespace like the following:
     "Action 1":"self.actions.mineBlock('oak_log', 2)",
     "Action 2":"self.actions.craftItem('oak_planks', 10, False)"
    """)
])

        self.observationChain = LLMChain(llm=self.llm, prompt=self.observationPrompt, output_key="observation", memory=None)
        self.collectChain = LLMChain(llm=self.llm, prompt=self.collectPrompt, output_key="plan", memory=None)
        self.materialChain = LLMChain(llm=self.llm, prompt=self.materialPrompt, output_key="materials", memory=None)

        self.overallChain = SequentialChain(
            chains=[self.observationChain,self.materialChain, self.collectChain],
            input_variables=["layout", 'health', 'hunger', 'inventory', 'position', 'nearbyEntities','retrievedPlans','failedPlan'],
            output_variables=["observation", "plan",'materials'],
            verbose=True
        )
    def generateCollectionPlan(self, layout, state, position, observationSpace):
    
        retrievedDocs = self.retriever.invoke(layout, filter={"source": "news"})

        # Combine retrieved plans into a single string
        retrievedContent = "\n".join([doc.page_content for doc in retrievedDocs])

        result = self.overallChain.invoke(input={
            "layout": layout,
            "health": state['health'],
            "position": position,
            "hunger": state['food'],
            "inventory": state['inventory'],
            'nearbyEntities': observationSpace['nearbyEntities'],
            'failedPlan':observationSpace['failedPlan'],
            'retrievedPlans': retrievedContent
        })
        actions_dict = fix_json_response(result['plan'])
        return actions_dict



