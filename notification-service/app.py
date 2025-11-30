from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_restx import Api, Resource, fields
from models import db, Notification
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
CORS(app)

api = Api(app, doc="/api-docs/", version="1.0",
          title="Notification Service",
          description="Sends notifications for transactions and user events.")

notif_model = api.model("Notification", {
    'id': fields.Integer(readOnly=True),
    'user_id': fields.Integer(required=True),
    'message': fields.String(required=True),
})

notif_ns = api.namespace("notifications", description="Notification operations")


@notif_ns.route("/")
class NotificationList(Resource):

    @notif_ns.marshal_list_with(notif_model)
    def get(self):
        return [n.to_dict() for n in Notification.query.all()]

    @notif_ns.expect(notif_model)
    @notif_ns.marshal_with(notif_model, code=201)
    def post(self):
        """Send notification"""
        data = request.json
        notif = Notification(
            user_id=data['user_id'],
            message=data['message']
        )
        db.session.add(notif)
        db.session.commit()
        return notif.to_dict(), 201


@app.route("/health")
def health():
    return jsonify({'status': 'healthy', 'service': Config.SERVICE_NAME})


@app.cli.command("create-db")
def create_db():
    with app.app_context():
        db.create_all()
        print("Database created for Notification Service.")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=Config.PORT, debug=True)
