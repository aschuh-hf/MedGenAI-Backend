from flask import Blueprint, request, jsonify
from middleware.auth import require_auth
from models import Users, UserGuess, Images
from __init__ import db
from services.game_service import GameService
import random

game_bp = Blueprint('game', __name__)
game_service = GameService()

@game_bp.route('/initialize-classic-game', methods=['POST'])
@require_auth
def initialize_classic_game():
    """
    Initialize a classic game where users guess between real and AI images
    """
    try:
        data = request.get_json()
        image_count = data.get('imageCount', 10)  # Default to 10 images if not specified
        user_id = request.user_id  # From @require_auth decorator

        print(f"Initializing classic game for user {user_id}")
        print(f"Image count: {image_count}")
        
        # Ensure user exists in database
        user = Users.query.filter_by(user_id=user_id).first()
        if not user:
            return jsonify({
                'error': 'User not found',
                'status': 'error'
            }), 404
        
        print(f"User found: {user}")
        
        # Initialize classic game - will get a mix of real and AI images
        game_id, images, code = game_service.initialize_classic_game(
            image_count=image_count,
            user_id=user.user_id
        )

        # Update user's games_started count
        user.games_started += 1
        db.session.commit()

        return jsonify({
            'gameId': game_id,
            'images': images,
            'status': 'success',
            'gameCode': code
        })

    except ValueError as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 400
    except Exception as e:
        print(f"Error in initialize_classic_game: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@game_bp.route('/initialize-single-game-with-code', methods=['POST'])
@require_auth
def initialize_single_game_with_code():
    """
    Initialize a single game with a specified game code
    """
    try:
        data = request.get_json()
        game_code = data.get('gameCode')
        image_count = data.get('imageCount', 10)
        user_id = request.user_id  # From @require_auth decorator

        if not game_code:
            return jsonify({
                'error': 'Game code is required',
                'status': 'error'
            }), 400

        print(f"Image count: {image_count}")
    
        print(f"Initializing game with code {game_code} for user {user_id}")
        
        # Ensure user exists in database
        user = Users.query.filter_by(user_id=user_id).first()
        if not user:
            return jsonify({
                'error': 'User not found',
                'status': 'error'
            }), 404
        
        print(f"User found: {user}")
        
        # Initialize game with code
        game_id, images, game_code = game_service.initialize_game_with_code(
            game_code=game_code,
            user_id=user.user_id,
            image_count=image_count
        )

        db.session.commit()

        return jsonify({
            'gameId': game_id,
            'images': images,
            'status': 'success',
            'gameCode': game_code
        })

    except ValueError as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 400
    except Exception as e:
        print(f"Error in initialize_single_game_with_code: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@game_bp.route('/finish-classic-game', methods=['POST'])
@require_auth
def finish_classic_game():
    """
    Finish a classic game and update user's score, as well as the image guesses in userGuesses Table
    POST request with the following fields:
    gameId: The ID of the game to finish
    userGuesses: A list of user guesses for the game - each guess is a dictionary with the following fields:
        imageId: The ID of the image the user guessed
        userGuessType: The type of guess the user made (real or ai)
        correct: Whether the guess was correct or not
    """
    try:
        data = request.get_json()
        game_id = data.get('gameId')
        user_id = request.user_id
        user_guesses = data.get('userGuesses', [])
        
        if not game_id or not user_guesses:
            return jsonify({
                'error': 'Missing required fields',
                'status': 'error'
            }), 400
            
        # Finish game and get results
        results = game_service.finish_classic_game(
            game_id=game_id,
            user_id=user_id,
            user_guesses=user_guesses
        )
        
        return jsonify(results)
        
    except ValueError as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 400
    except Exception as e:
        print(f"Error in finish_classic_game: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500
    
@game_bp.route('/get-game/<game_id>', methods=['GET'])
@require_auth
def get_game(game_id):
    """
    Get a game for the user
    """
    try:
        user_id = request.user_id
        game = game_service.get_game(game_id, user_id)

        return jsonify(game)
    except Exception as e:
        print(f"Error in get_game: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@game_bp.route('/competition-single-game', methods=['GET'])
@require_auth
def get_competition_single_game():
    """
    Get a random competition game
    """
    try:
        user_id = request.user_id
        
        # Ensure user exists in database
        user = Users.query.filter_by(user_id=user_id).first()
        if not user:
            return jsonify({
                'error': 'User not found',
                'status': 'error'
            }), 404
            
        # Get a random competition game
        game_id, images = game_service.get_random_competition_game(user_id)
        
        # Update user's games_started count
        user.games_started += 1
        db.session.commit()
        
        return jsonify({
            'gameId': game_id,
            'images': images,
            'status': 'success'
        })
        
    except ValueError as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 400
    except Exception as e:
        print(f"Error in get_competition_single_game: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

