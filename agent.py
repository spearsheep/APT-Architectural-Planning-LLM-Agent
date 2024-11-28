
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
import os
import httpx
from langchain_openai import AzureChatOpenAI
from fixJson import fix_json_response
import json
import time
from datetime import datetime
import base64
import requests
import re
import llmAlgorithms
from memory import MemoryDatabase
from javascript import require, On, Once, AsyncTask, once, off
import math
from actions import Actions
vec3 = require("vec3")


class Agent:

    def __init__(self, playerUsername, botName, serverHost, serverPort, reconnect=True):
        self.playerUsername = playerUsername
        self.botName = botName
        self.serverHost = serverHost
        self.serverPort = serverPort
        self.reconnect = reconnect
        self.bot = None
        self.locationRequested = False
        self.botArgs = {
            "host": serverHost,
            "port": serverPort,
            "username": botName,
            "hideErrors": False,
        }
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.llm =  ChatOpenAI(model="gpt-4o",api_key=self.api_key,
            temperature=0.8)
        # self.algorithm = llmAlgorithms.LLMDecisionMaker(self.llm)
        self.algorithm = llmAlgorithms.singleAgentDecisionMaker(self.llm)
        
        
        self.createBot()
        

    def createBot(self):
        mineflayer = require("mineflayer")
        pathfinder = require('mineflayer-pathfinder')
        collectBlockPlugin = require('mineflayer-collectblock')
        blockFinderPlugin = require('mineflayer-blockfinder')
        pvp = require('mineflayer-pvp').plugin
        viewer = require('prismarine-viewer').mineflayer
        puppeteer = require('puppeteer')
        goals = pathfinder.goals
        self.bot = mineflayer.createBot(self.botArgs)
        self.bot.loadPlugin(pathfinder.pathfinder)
        self.bot.loadPlugin(collectBlockPlugin.plugin)
        self.bot.loadPlugin(blockFinderPlugin)
        self.bot.loadPlugin(blockFinderPlugin)
        self.bot.loadPlugin(pvp)
        self.mcData = require('minecraft-data')(self.bot.version)
        self.movements = pathfinder.Movements(self.bot, self.mcData)
        self.movements.canDig = False
        self.bot.pathfinder.setMovements(self.movements)
        self.actions = Actions(self.bot, self.mcData, self.movements,self.playerUsername)
        self.serverPortViewer = 3100
        self.viewer= viewer(self.bot, { 'port': self.serverPortViewer,'firstPerson': True })
        self.browser = puppeteer.launch({'executablePath': 'C:/Users/junyu/chrome/win64-129.0.6668.100/chrome-win64/chrome.exe'})
        self.page = self.browser.newPage()
        self.page.goto(f'http://localhost:{self.serverPortViewer}')
        self.startEvents()
        self.goals = goals
        
        return self.bot
    
    def log(self, message):
        print(f"[{self.bot.username}] {message}")

    def startEvents(self):
        bot = self.bot
        botName = self.botName
        reconnectState = {"reconnect": self.reconnect}

        @On(bot, "login")
        def handleLogin(this):

            botSocket = bot._client.socket
            print(f"[{botName}] Logged in to {botSocket.server if botSocket.server else botSocket._host }")
        
        # @On(bot, 'spawn')
        # def onSpawn(*args):
        #     viewer(bot, { 'port': 3007,'firstPerson': True })
      

        @On(bot, "kicked")
        def handleKicked(this, reason, loggedIn):
            if loggedIn:
                print(f"[{botName}] Kicked whilst trying to connect: {reason}")


        @On(bot, "messagestr")
        def handleMessagestr(this, message, messagePosition, jsonMsg, sender, verified=None):
            if messagePosition == "chat" and "quit" in message:
                reconnectState["reconnect"] = False
                this.quit()
            elif messagePosition == "chat" and'come' in message:
                localPlayers = bot.players
                for player in localPlayers:
                        playerData = localPlayers[player]
                        if playerData["uuid"] == sender:
                            target = localPlayers[player].entity
                            
                if not target:
                    bot.chat("I don't see you !")
                    return
                pos = target.position

                bot.pathfinder.setGoal(self.goals.GoalNear(pos.x, pos.y, pos.z, 1))
            elif messagePosition == "chat" and'creative' in message:
                bot.chat('/gamemode creative')
            elif messagePosition == "chat" and'survival' in message:
                bot.chat(f'/gamemode survival {str(self.bot.username)}')
            elif messagePosition == "chat" and'day' in message:
                bot.chat('/time set day')
            elif messagePosition == "chat" and'sunny' in message:
                bot.chat('/weather clear')
            elif messagePosition == "chat" and'get my position' in message:
                pos = bot.entity.position
                bot.chat(f"My current location is X: {pos.x:.2f}, Y: {pos.y:.2f}, Z: {pos.z:.2f}")
  
        @On(bot, "end")
        def handleEnd(this, reason):
            print(f"[{botName}] Disconnected: {reason}")
            # Turn off old events
            off(bot, "login", handleLogin)
            off(bot, "kicked", handleKicked)
            off(bot, "messagestr", handleMessagestr)

            # Reconnect if the reconnect flag is set to True
            if reconnectState["reconnect"]:
                print(f"[{botName}] Attempting to reconnect")
                self.createBot()

            # Last event listener
            off(bot, "end", handleEnd)
    

    def execute_actions(self, actions_dict, max_attempts=3):
        results = []
        all_successful = True

        for action_name, action_code in actions_dict.items():
            attempts = 0
            success = False
            
            while attempts < max_attempts and not success:
                try:
                    attempts += 1
                    print(f"Attempt {attempts} for {action_name}: {action_code}")
                    exec(action_code)
                    success = True
                except Exception as e:
                    print(f"Error executing {action_name} on attempt {attempts}: {e}")
                    if attempts >= max_attempts:
                        print(f"{action_name} failed after {max_attempts} attempts.")
            
            results.append((action_name, action_code, success))
            
            if not success:
                all_successful = False

        return results, all_successful

    def take_screenshot(self, path='screenshot.png'):
        self.page.screenshot({'path': path})

    def complete_task(self, task, max_iterations=3):
        failedPlanText = "There is no previous plan"  # Initialize with the default value for the first iteration

        for iteration in range(max_iterations):
            state = self.actions.getState()
            observationSpace = self.actions.observe(3)
            position = self.bot.entity.position

            # Add the failed plan to the observation space
            observationSpace['failedPlan'] = failedPlanText

            # Generate the plan based on the current state, position, and observations
            plan = self.algorithm.generatePlan(task, state, position, observationSpace)

            # Execute the generated plan
            results, all_successful = self.execute_actions(plan)

            if all_successful:
                # Store the successful plan in the memory database
                infoString = (str(state['health']) + ", " +
                            str(position) + ", " +
                            str(state['food']) + ", " +
                            str(state['inventory']) + ", " +
                            str(observationSpace['nearbyEntities']))
                self.algorithm.memoryDatabase.store_plan(task, infoString, plan)
                return results, True  # Task completed successfully

            # If actions fail, reflect on the failed plan and retry
            failedPlanText = "\n".join([f"Action: {name}, Code: {code}" for name, code, success in results])

            print(f"Iteration {iteration + 1} failed. Re-evaluating plan.")
            print(f"Failed plan: {failedPlanText}")

        return results, False  # Task could not be completed after maximum iterations

    

class ArchitectAgent(Agent):
    def __init__(self, playerUsername, botName, serverHost, serverPort, reconnect=True,max_reattempts=3):
        super().__init__(playerUsername, botName, serverHost, serverPort, reconnect)
        self.algorithm = llmAlgorithms.ArchitectLLMAlgorithm(self.llm)
        self.listen()
        self.blueprint = None
        self.size = None
        self.max_reattempts = max_reattempts  # User-defined number of reattempts
        self.initialPosition = None
        self.reflection = None
    
    def listen(self):
        bot = self.bot
        botName = self.botName

        @On(bot, "messagestr")
        def handleMessagestr(this, message, messagePosition, jsonMsg, sender, verified=None):


            if messagePosition == "chat" and 'Materials delivered' in message and self.bot.players.Gatherer.uuid == sender:
                bot.chat('start receiving')
                self.receiveMaterials()

            if messagePosition == "chat" and 'Received all the materials' in message and botName == 'Architect':
                bot.chat('start building')
                self.build()

    
    def designBlueprint(self, structure=None, useImage=False, imageUrl=None,memory =True):
        # Generate the blueprint for the structure
        self.bot.chat('Start designing blueprint')
        blueprint,size = self.algorithm.generateBlueprint(structure=structure, useImage=useImage, imageUrl=imageUrl,memory=memory)
        self.bot.chat('Finished designing blueprint')
        self.blueprint = blueprint
        self.structure = structure
        # self.size = vec3(size)
        return size,blueprint
    
    def receiveMaterials(self):
        time.sleep(2)
        received = False
        try:
            for entity_id in self.bot.entities:
                entity = self.bot.entities[entity_id]
                if not entity or entity.position is None:
                    continue  # Skip entities without a valid position

                if entity.name == 'item':
                    print(entity)
                    self.bot.collectBlock.collect(entity, timeout=1000)
            self.bot.chat("Received all the materials")
            received = True
        except Exception as e:
            self.bot.chat(f"An error occurred while receiving materials")
        return received
    
    def build(self, blueprint):
        try:
            self.initialPosition = self.bot.entity.position.floor()
            exec_context = {
            'self': self,
            'layout': [],
        }
            exec(blueprint,exec_context)
            return True  # Return True if everything succeeds
        except Exception as e:
            self.bot.chat(str(e))
            return False  # Return False if any error occurs

    def designAndBuild(self, structure=None, useImage=False, imageUrl=None, n = 3, memory =True):
        # Generate the initial blueprint
        self.size, self.blueprint  = self.designBlueprint(structure,useImage,imageUrl, memory =memory)
        execution = self.build(self.blueprint)

        # If initial build is not successful, reattempt designBlueprint up to n times
        if not execution:
            self.bot.chat("code failed to execute")
            execution_attempts = 0
            while not execution and execution_attempts < n:
                execution_attempts += 1
                self.size, self.blueprint = self.designBlueprint(structure,useImage,imageUrl, memory =memory)
                execution = self.build(self.blueprint)
        if execution:
            print(f"Initial Blueprint: {self.blueprint}")
            self.bot.chat("code executed correctly")
        else:
            self.bot.chat(f"code failed to execute after {n} times")

        
        return execution
        
    
    def addMemory(self,success= True):
        position = self.bot.entity.position

        if success:
            self.bot.chat('Finished gathering materials')
            # Store the successful plan in the memory database
            infoString = (str(position) )

            self.algorithm.memoryDatabase.store_plan(self.structure, infoString, self.blueprint)
            return success  # Task completed successfully
    
    def addMemoryByHuman(self,structure, blueprint):
        state = self.actions.getState()
        self.bot.chat('Finished gathering materials')
        # Store the successful plan in the memory database
        infoString = (str(state['health']))

        self.algorithm.memoryDatabase.store_plan(structure, infoString,blueprint)
        print('added')

    def visualInspection(self, size, initialPosition):
        # Calculate the center of the structure

        # Use regular expression to extract numbers within parentheses
        match = re.search(r'vec3\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', size)

        if match:
            # Parse values as integers
            x = int(match.group(1))
            y = int(match.group(2))
            z = int(match.group(3))
        size = vec3(x,y,z)
        structureCenter = initialPosition.offset(size.x / 2, 0, size.z / 2)

        # Determine the maximum dimension of the structure
        maxDimension = max(size.x, size.z)

        # Calculate a distance to move back (1.5 to 2 times the max dimension)
        distanceToMoveBack = maxDimension * 2  # Adjust this multiplier if needed

        # Define the four directions with position offsets and direction names
        directions = {
            "north": vec3(0, 0, -distanceToMoveBack),
            "south": vec3(0, 0, distanceToMoveBack),
            "east": vec3(distanceToMoveBack, 0, 0),
            "west": vec3(-distanceToMoveBack, 0, 0)
        }

        # List to store screenshot file paths
        screenshot_paths = []

        # Loop through each direction
        for direction_name, position_offset in directions.items():
            # Calculate the target position based on the position_offset
            targetPosition = structureCenter.offset(position_offset.x, 0, position_offset.z)

            # Move to the target position using pathfinding
            self.actions.pathfinding(targetPosition)
            attempts = 0
            distanceFlag = True

            # Ensure that the bot has reached the target position before taking a screenshot
            while distanceFlag:
                while attempts < 3:
                    try:
                        distance = self.bot.entity.position.distanceTo(targetPosition)
                        if distance < 2:  # Within 2 blocks of the target
                            distanceFlag = False
                        break  # If successful, exit the loop
                    except Exception as e:
                        self.bot.chat("Retrying computing distance...")
                        attempts += 1
                        if attempts >= 3:
                            self.bot.chat("Distance cannot be computed")
                    time.sleep(1)
            time.sleep(3)

            # Make the bot look at the center of the structure (mid height)
            self.bot.lookAt(structureCenter.offset(0, size.y / 2, 0))

            time.sleep(2)

            # Generate a unique screenshot filename based on the direction name and current time
            screenshot_directory = './agentVisualRecord'
            if not os.path.exists(screenshot_directory):
                os.makedirs(screenshot_directory)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Current date and time
            screenshot_filename = f"{screenshot_directory}/{direction_name}_view_{timestamp}.png"

            # Call your screenshot function with the appropriate filename
            self.take_screenshot(screenshot_filename)

            # Append the screenshot path to the list
            screenshot_paths.append(screenshot_filename)

        # Return the list of screenshot paths
        return screenshot_paths

    def ReflectAndBuild(self,imagePaths, initial_structure, blueprint, n=3):
        self.blueprint, self.reflection = self.algorithm.selfReflect(imagePaths, initial_structure, blueprint)
        execution = self.build(self.blueprint)
        # If initial build is not successful, reattempt designBlueprint up to n times
        if not execution:
            self.bot.chat(f"code failed to execute")
            execution_attempts = 0
            while not execution and execution_attempts < n:
                execution_attempts += 1
                self.blueprint, self.reflection = self.algorithm.selfReflect(imagePaths, initial_structure, blueprint)
                execution = self.build(self.blueprint)
        if execution:
            print(f"Reflected Blueprint: {self.blueprint}")
            self.bot.chat("code executed correctly")
        else:
            self.bot.chat(f"code failed to execute after {n} times")

        
        
        return execution



    def feedbackLoop(self, initial_structure,useImage=False, imageUrl=None, memory =True):
        """Executes the blueprint, and if it fails, gathers feedback and re-generates the blueprint."""
        
        success = False
        execution = False
        execution = self.designAndBuild(structure=initial_structure, useImage=useImage, imageUrl=imageUrl, memory = memory)
        reattempts=0
        if not execution:
            return False
        
        while not success and reattempts < self.max_reattempts:
            # User input for feedback after each build attempt
            user_input = input("Was the build successful? (yes/no): ").strip().lower()

            # If the user confirms success, stop the loop
            if user_input == "yes":
                success = True
                break
            elif user_input == "no":
                # Visual inspection and reflection to generate an improved blueprint
                print("Visual inspection in progress")
                imagePaths = self.visualInspection(self.size, self.initialPosition)
                print("Regenerating blueprint based on feedback...")
                user_input = input("I am ready to rebuild")
                execution = self.ReflectAndBuild(imagePaths, initial_structure,self.blueprint, n=3)
                if not execution:
                    return False
                reattempts += 1
            else:
                print("Invalid input, please enter 'yes' or 'no'.")

        if success:
            print("Blueprint executed successfully after feedback!")
        else:
            print("Max reattempts reached. Failed to execute the blueprint correctly.")

        return success

        



    
    


class GathererAgent(Agent):
    def __init__(self, playerUsername, botName, serverHost, serverPort, reconnect=True):
        super().__init__(playerUsername, botName, serverHost, serverPort, reconnect)
        self.algorithm = llmAlgorithms.GathererLLMAlgorithm(self.llm)
        self.listen()

    def collectMaterial(self, task, layout,max_iterations =3):
        failedPlanText = "There is no previous plan"  # Initialize with the default value for the first iteration

        for iteration in range(max_iterations):
            state = self.actions.getState()
            observationSpace = self.actions.observe(3)
            position = self.bot.entity.position

            # Add the failed plan to the observation space
            observationSpace['failedPlan'] = failedPlanText

            # Generate the plan based on the current state, position, and observations
            gatherPlan= self.algorithm.generateCollectionPlan(layout, state, position, observationSpace)

            # Execute the generated plan
            results, all_successful = self.execute_actions(gatherPlan)

            if all_successful:
                self.bot.chat('Finished gathering materials')
                # Store the successful plan in the memory database
                infoString = (str(state['health']) + ", " +
                            str(position) + ", " +
                            str(state['food']) + ", " +
                            str(state['inventory']) + ", " +
                            str(observationSpace['nearbyEntities']))
                self.algorithm.memoryDatabase.store_plan(task, infoString, gatherPlan)
                return results, True  # Task completed successfully

            # If actions fail, reflect on the failed plan and retry
            failedPlanText = "\n".join([f"Action: {name}, Code: {code}" for name, code, success in results])

            print(f"Iteration {iteration + 1} failed. Re-evaluating plan.")
            print(f"Failed plan: {failedPlanText}")

        return results, False  # Task could not be completed after maximum iterations
    
    def listen(self):
        bot = self.bot
        botName = self.botName

        @On(bot, "messagestr")
        def handleMessagestr(this, message, messagePosition, jsonMsg, sender, verified=None):
            if messagePosition == "chat" and 'Finished gathering materials' in message and botName == 'Gatherer':
                self.deliverMaterials()
            elif messagePosition == "chat" and 'Received all the materials' in message and self.bot.players.Architect.uuid == sender:
                self.actions.pathfinding(self.bot.players.Architect.entity.position.offset(30,0,0))
    
    def deliverMaterials(self):
        architectPosition = self.bot.players.Architect.entity.position
        self.actions.pathfinding(architectPosition)
        attempts = 0
        distanceFlag = True
        while distanceFlag :
            while attempts < 3:
                try:
                    distance = self.bot.entity.position.distanceTo(architectPosition)
                    if distance <2:
                        distanceFlag=False
                    break  # If successful, exit the loop
                except Exception as e:
                    self.bot.chat("retrying computing distance")
                    attempts += 1
                    if attempts >= 3:
                        self.bot.chat("distance cannot be computed")
            time.sleep(1)
        for item in self.bot.inventory.items():
            self.bot.tossStack(item)
        self.bot.chat("Materials delivered")

