from typing import Optional, Tuple
CAPTAININTRO = "**Answer all the following questions. If you don’t know an answer, ask your favorite strategist to explain!**"
CAPTAINQUESTIONS = (
    "What is your IGN and why would you like to become a captain?",
    "How long have you been in ANO and how do you like it here?",
    "Do you see yourself participating in HQ wars?",
    "Do you currently have any war builds? What other builds are you interested in playing?",
    "How do you dodge tower Aura on your class?",
    "What consumables do you need for your war build? Who can you ask for them?",
    "How do you know who stands closer to the tower before it starts attacking?",
    "Do you have a Well of Power or Totem of Tales for use in wars?",
    "Have you completed Realm of Light 5 to use the bracelet Double Vision?",
    "How do you queue a territory for a war?",
    "Where is our HQ? What are 4 other important territories?",
    "Where are the FFA zones?",
    "A strategist tells you to “queue HMI”. What territory are they referring to?",
    "Durum Barley Islet is taken. Why is it urgent that we reclaim it?",
    "Who do you notify if it is taken? What command can you use in military chat to do so?",
    "While we are being attacked, who do you listen to? Where do you look for communication?",
)

def makeCaptainTopic(applicantid: int, questionindex: int, pendinganswerid: Optional[int] = None, answerids: Tuple[int, ...] = ()) -> str:
    answeridstext = ",".join(str(answerid) for answerid in answerids)
    return "|".join(("captain-checklist", str(applicantid), str(questionindex), str(pendinganswerid or 0), answeridstext))

def parseCaptainTopic(topic: Optional[str]) -> Optional[Tuple[int, int, Optional[int], Tuple[int, ...]]]:
    if not topic:
        return None
    try:
        prefix, applicantid, questionindex, pendinganswerid, answerids = topic.split("|", 4)
        if prefix != "captain-checklist":
            return None
        parsedanswerids = tuple(int(answerid) for answerid in answerids.split(",") if answerid)
        return int(applicantid), int(questionindex), int(pendinganswerid) or None, parsedanswerids
    except ValueError:
        return None

def chunkCaptainReport(text: str, limit: int = 1900) -> Tuple[str, ...]:
    chunks = []
    while len(text) > limit:
        splitat = text.rfind("\n", 0, limit)
        if splitat >= 0:
            splitat += 1
        else:
            splitat = text.rfind(" ", 0, limit)
            if splitat >= 0:
                splitat += 1
        if splitat <= 0:
            splitat = limit
        chunks.append(text[:splitat])
        text = text[splitat:]
    if text:
        chunks.append(text)
    return tuple(chunks)

def buildCaptainReport(applicationnumber: int, applicantid: int, answers: Tuple[str, ...], limit: int = 1900) -> Tuple[str, ...]:
    report = [f"**Captain Checklist #{applicationnumber}** - <@{applicantid}>\n"]
    for index, question in enumerate(CAPTAINQUESTIONS):
        answer = answers[index] if index < len(answers) else "[Answer unavailable]"
        report.append(f"\n**{index + 1}. {question}**\n{answer}\n")
    return chunkCaptainReport("".join(report), limit)