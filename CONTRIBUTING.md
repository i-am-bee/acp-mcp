# Contributing to ACP

🎉 Thank you for considering contributing to the Agent Communication Protocol (ACP) ecosystem! Your contributions help shape the future of agent interoperability and make ACP better for everyone.

Before you get started, please take a moment to review our [Contribute Guide](https://agentcommunicationprotocol.dev/about/contribute) to understand the different ways you can get involved.

## 🚀 How to Contribute

We welcome all kinds of contributions:

- 💡 Share Use Cases — Help ground ACP in real-world scenarios.
- 🛠️ Implement Examples — Show ACP in action with practical code.
- 🐛 Report Issues — Found a bug or something unclear? Let us know.
- 🚀 Propose Enhancements — Have ideas to improve ACP? Share them!
- 📄 Improve Documentation — Clear docs help everyone.
- 🔧 Core Development — Contribute directly to the SDKs and protocol and more.

No contribution is too small!

## Fork the repository

To contribute code:

1. Fork this repository.
2. Clone your fork:
```bash
git clone https://github.com/your-username/acp-mcp.git
```
1. Install dependencies using uv:
```bash
uv sync
```

If you're unfamiliar with `uv`, check out our [Quickstart](https://agentcommunicationprotocol.dev/introduction/uv-primer).

## Running Tests

Before submitting a PR, make sure all tests pass:

- **E2E Tests**:
```bash
uv run pytest tests/e2e
```

## 📝 Commit Guidelines
We follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) to keep our commit history clean and meaningful.

Example commit messages:

- `feat(server): add support for agent timeouts`
- `docs: update contributing guidelines`

Use clear, descriptive messages to explain what and why.
