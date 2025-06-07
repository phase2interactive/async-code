import Image from "next/image";

export default function Home() {
    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 px-6 py-4">
                <div className="flex items-center justify-between max-w-7xl mx-auto">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-black rounded-full flex items-center justify-center">
                            <span className="text-white text-sm font-bold">C</span>
                        </div>
                        <span className="text-xl font-semibold">Codex</span>
                    </div>
                    <div className="flex items-center gap-6">
                        <nav className="flex items-center gap-6">
                            <a href="#" className="text-gray-600 hover:text-gray-900 font-medium">
                                Environments
                            </a>
                            <a href="#" className="text-gray-600 hover:text-gray-900 font-medium">
                                Docs
                            </a>
                        </nav>
                        <div className="w-8 h-8 bg-gradient-to-br from-orange-400 to-pink-500 rounded-full flex items-center justify-center">
                            <span className="text-white text-xs font-bold">PRO</span>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-4xl mx-auto px-6 py-12">
                <h1 className="text-4xl font-bold text-center mb-12 text-gray-900">
                    What are we coding next?
                </h1>

                {/* Editable Text Area */}
                <div className="mb-6">
                    <div
                        contentEditable
                        className="w-full px-6 py-6 text-base border border-gray-200 rounded-2xl bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent min-h-[120px] leading-relaxed"
                        suppressContentEditableWarning={true}
                    >
                        See how /demos/tokenize is now a top-tier interactive learning demo? Make /demos/embeddings the same thing.
                        <br />
                        <br />
                        Also, from /demos/embeddings, I want to hardcode the embeddings themselves and have some pre-fabbed sentences, so that we don&apos;t have to have YET another public route on my site that points at my OpenAI credits.
                    </div>
                </div>

                {/* Controls */}
                <div className="flex items-center justify-between mb-8">
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <svg className="w-4 h-4 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M4 2a2 2 0 00-2 2v11a2 2 0 002 2h12a2 2 0 002-2V4a2 2 0 00-2-2H4zm0 2h12v11H4V4z" clipRule="evenodd" />
                            </svg>
                            <select className="text-sm border-none bg-transparent focus:outline-none text-gray-700 font-medium">
                                <option>zackproser/portfolio</option>
                            </select>
                            <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                            </svg>
                        </div>
                        <div className="flex items-center gap-2">
                            <svg className="w-4 h-4 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M7.707 3.293a1 1 0 010 1.414L5.414 7H11a7 7 0 017 7v2a1 1 0 11-2 0v-2a5 5 0 00-5-5H5.414l2.293 2.293a1 1 0 11-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                            <select className="text-sm border-none bg-transparent focus:outline-none text-gray-700 font-medium">
                                <option>main</option>
                            </select>
                            <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                            </svg>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <button className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                            Ask
                        </button>
                        <button className="px-4 py-2 text-sm font-medium text-white bg-black rounded-lg hover:bg-gray-800 transition-colors">
                            Code
                        </button>
                    </div>
                </div>

                {/* Tabs */}
                <div className="mb-8">
                    <div className="flex gap-8 border-b border-gray-200">
                        <button className="pb-3 px-1 border-b-2 border-black font-semibold text-gray-900">
                            Tasks
                        </button>
                        <button className="pb-3 px-1 text-gray-500 hover:text-gray-700">
                            Archive
                        </button>
                    </div>
                </div>

                {/* Task List */}
                <div className="space-y-4">
                    {/* Task 1 */}
                    <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between">
                            <div className="flex-1">
                                <div className="flex items-center gap-2 mb-2">
                                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                                    <h3 className="font-semibold text-gray-900">
                                        Resolve merge issue
                                    </h3>
                                </div>
                                <p className="text-sm text-gray-500">
                                    1 min ago · zackproser/portfolio
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Task 2 */}
                    <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between">
                            <div className="flex-1">
                                <h3 className="font-semibold text-gray-900 mb-2">
                                    Remove &apos;From colleagues, clients and collaborators&apos; text
                                </h3>
                                <p className="text-sm text-gray-500">
                                    15 min ago · zackproser/portfolio
                                </p>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-sm px-2 py-1 bg-green-100 text-green-700 rounded">
                                    Open
                                </span>
                                <span className="text-sm text-green-600">+6</span>
                                <span className="text-sm text-red-600">-6</span>
                            </div>
                        </div>
                    </div>

                    {/* Task 3 */}
                    <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between">
                            <div className="flex-1">
                                <h3 className="font-semibold text-gray-900 mb-2">
                                    Update terminal prompt behavior
                                </h3>
                                <p className="text-sm text-gray-500">
                                    15 min ago · zackproser/portfolio
                                </p>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-sm px-2 py-1 bg-purple-100 text-purple-700 rounded">
                                    Merged
                                </span>
                                <span className="text-sm text-green-600">+3</span>
                                <span className="text-sm text-red-600">-1</span>
                            </div>
                        </div>
                    </div>

                </div>
            </main>
        </div>
    );
}
